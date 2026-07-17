<template>
  <div class="station-detail">
    <el-page-header @back="$router.back()" content="泵站详情" />
    <el-card style="margin-top:16px">
      <template #header>{{ stationName }} — 设备概览</template>
      <el-row :gutter="16">
        <el-col :span="6" v-for="p in pumps" :key="p.device_id">
          <el-card shadow="hover" class="pump-card" @click="$router.push(`/pump/${p.device_id}`)">
            <div class="hi-circle" :style="{ borderColor: hiColor(p.current_hi) }">
              <span class="hi-num">{{ p.current_hi ?? '--' }}</span>
            </div>
            <p class="pump-name">{{ p.device_id }}</p>
            <p class="pump-type">{{ p.pump_type }}</p>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const stationName = ref('泵站 ' + route.params.id)
const pumps = ref([])

const hiColor = (hi) => {
  if (hi == null) return '#898781'
  if (hi >= 85) return '#008300'
  if (hi >= 70) return '#eda100'
  if (hi >= 50) return '#eb6834'
  return '#d03b3b'
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/pumps')
    pumps.value = data.slice(0, 8)
  } catch (e) { console.warn('获取泵站数据失败') }
})
</script>

<style scoped>
.station-detail { padding: 16px; }
.pump-card { text-align: center; cursor: pointer; }
.pump-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
.hi-circle {
  width: 64px; height: 64px; border-radius: 50%; border: 4px solid;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 8px;
}
.hi-num { font-size: 20px; font-weight: 700; }
.pump-name { font-size: 13px; font-weight: 600; margin: 4px 0; }
.pump-type { font-size: 11px; color: #898781; }
</style>
