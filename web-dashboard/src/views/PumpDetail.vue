<template>
  <div class="pump-detail" v-if="pump">
    <el-page-header @back="$router.back()" :content="pump.device_id" />

    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="8">
        <el-card>
          <template #header>健康状态</template>
          <div class="hi-display">
            <span class="hi-value" :style="{ color: hiColor(pump.current_hi) }">
              {{ pump.current_hi ?? '--' }}
            </span>
            <span class="hi-grade">{{ pump.hi_grade ?? '--' }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>设备信息</template>
          <p>型号：{{ pump.pump_type }}</p>
          <p>额定流量：{{ pump.rated_flow }} m³/h</p>
          <p>额定扬程：{{ pump.rated_head }} m</p>
          <p>位置：{{ pump.country }}</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>操作</template>
          <el-button type="primary" @click="analyzeRCA">根因分析</el-button>
          <el-button type="warning" @click="predictRUL">RUL 预测</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top:16px">
      <template #header>HI 退化趋势</template>
      <div ref="chartRef" style="height:300px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'

const route = useRoute()
const pump = ref(null)
const chartRef = ref(null)

const hiColor = (hi) => {
  if (hi >= 85) return '#008300'
  if (hi >= 70) return '#eda100'
  if (hi >= 50) return '#eb6834'
  return '#d03b3b'
}

const analyzeRCA = async () => {
  const { data } = await axios.post(`/api/pumps/${route.params.id}/rca`, { current_data: {} })
  alert('根因分析结果：' + JSON.stringify(data.root_causes?.slice(0, 1), null, 2))
}

const predictRUL = async () => {
  const { data } = await axios.post(`/api/pumps/${route.params.id}/rul`, { hi_sequence: [85,84,82,80,78] })
  alert(`预估剩余寿命：${data.estimated_rul_days} 天`)
}

onMounted(async () => {
  try {
    const { data } = await axios.get(`/api/pumps/${route.params.id}`)
    pump.value = data
    await nextTick()
    if (chartRef.value) {
      const chart = echarts.init(chartRef.value)
      chart.setOption({
        xAxis: { type: 'category', data: ['T-30','T-20','T-10','T-0'] },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [{ data: [95, 90, 82, 75], type: 'line', smooth: true,
          markLine: { data: [{ yAxis: 30, label: { formatter: '失效阈值' }, lineStyle: { color: '#d03b3b' } }] }
        }]
      })
    }
  } catch (e) {
    console.warn('获取设备详情失败')
  }
})
</script>

<style scoped>
.pump-detail { padding: 16px; }
.hi-display { text-align: center; padding: 20px; }
.hi-value { font-size: 48px; font-weight: 700; }
.hi-grade { font-size: 16px; color: #52514e; display: block; margin-top: 8px; }
</style>
