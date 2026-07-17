<template>
  <div class="global-map">
    <div class="map-placeholder">
      <p>全球泵群健康状态一张图</p>
      <p class="sub">GeoJSON 地图标注 {{ pumps.length }} 台泵位置（接入 Leaflet/Mapbox 后展示交互地图）</p>
    </div>

    <el-card class="pump-table">
      <template #header>设备列表</template>
      <el-table :data="pumps" stripe height="400">
        <el-table-column prop="device_id" label="设备编号" width="120" />
        <el-table-column prop="pump_type" label="泵型号" width="140" />
        <el-table-column label="健康指数" width="100">
          <template #default="{ row }">
            <el-tag :type="hiTagType(row.current_hi)">{{ row.current_hi ?? '--' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="HI 等级" width="100">
          <template #default="{ row }">
            <span :style="{ color: hiGradeColor(row.hi_grade) }">{{ row.hi_grade ?? '--' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="country" label="国家" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/pump/${row.device_id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const pumps = ref([])

const hiTagType = (hi) => {
  if (hi == null) return 'info'
  if (hi >= 85) return 'success'
  if (hi >= 70) return 'warning'
  return 'danger'
}

const hiGradeColor = (grade) => {
  const map = { '健康': '#008300', '关注': '#eda100', '警告': '#eb6834', '严重': '#e34948', '危险': '#d03b3b' }
  return map[grade] || '#898781'
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/pumps')
    pumps.value = data
  } catch (e) {
    console.warn('获取设备列表失败')
  }
})
</script>

<style scoped>
.global-map { padding: 16px; }
.map-placeholder {
  background: #e1e0d9; border-radius: 8px; padding: 40px; text-align: center; margin-bottom: 16px;
}
.map-placeholder p { font-size: 16px; color: #52514e; }
.map-placeholder .sub { font-size: 13px; color: #898781; margin-top: 8px; }
</style>
