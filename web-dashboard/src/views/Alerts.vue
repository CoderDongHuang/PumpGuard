<template>
  <div class="alerts">
    <el-page-header @back="$router.back()" content="告警历史" />
    <el-card style="margin-top:16px">
      <template #header>告警时间线（{{ alerts.length }} 条）</template>
      <el-timeline>
        <el-timeline-item
          v-for="a in alerts" :key="a.id"
          :timestamp="a.timestamp"
          :type="a.severity === 'P0' ? 'danger' : a.severity === 'P1' ? 'warning' : 'primary'"
        >
          <el-card shadow="hover">
            <p><strong>{{ a.device_id }}</strong> — {{ a.fault_type }}</p>
            <p style="color:#898781;font-size:13px">HI: {{ a.health_index }} | 置信度: {{ a.probability }}%</p>
            <p style="color:#52514e;font-size:13px">{{ a.suggested_action }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const alerts = ref([])

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/alerts')
    alerts.value = data
  } catch (e) {
    alerts.value = [
      { id: 'ALT-001', device_id: 'PUMP-0007', fault_type: '轴承内圈磨损', health_index: 45, probability: 89, severity: 'P1', suggested_action: '更换轴承SKF-6305，预计4小时', timestamp: '2026-07-18 09:30:00' },
      { id: 'ALT-002', device_id: 'PUMP-0042', fault_type: '不对中', health_index: 62, probability: 76, severity: 'P2', suggested_action: '激光对中仪校正联轴器，预计2小时', timestamp: '2026-07-18 08:15:00' },
    ]
  }
})
</script>

<style scoped>
.alerts { padding: 16px; }
</style>
