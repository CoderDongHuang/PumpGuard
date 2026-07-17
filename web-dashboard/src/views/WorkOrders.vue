<template>
  <div class="workorders">
    <el-page-header @back="$router.back()" content="工单管理" />
    <el-card style="margin-top:16px">
      <template #header>
        <el-row justify="space-between">
          <span>工单列表（{{ orders.length }} 条）</span>
          <el-button type="primary" size="small" @click="refresh">刷新</el-button>
        </el-row>
      </template>
      <el-table :data="orders" stripe>
        <el-table-column prop="id" label="工单号" width="100" />
        <el-table-column prop="device_id" label="设备" width="110" />
        <el-table-column prop="fault_type" label="故障类型" width="150" />
        <el-table-column label="紧急程度" width="90">
          <template #default="{ row }">
            <el-tag :type="severityTag(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_engineer" label="工程师" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" v-if="row.status==='pending'" @click="assign(row)">派单</el-button>
            <el-button size="small" type="success" v-if="row.status==='in_progress'" @click="complete(row)">完成</el-button>
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const orders = ref([])

const severityTag = (s) => ({ P0: 'danger', P1: 'warning', P2: '', P3: 'info' }[s] || '')
const statusTag = (s) => ({ pending: 'warning', in_progress: 'primary', completed: 'success', cancelled: 'info' }[s] || '')
const statusText = (s) => ({ pending: '待处理', in_progress: '处理中', completed: '已完成', cancelled: '已取消' }[s] || s)

const refresh = async () => {
  try {
    const { data } = await axios.get('/api/workorders')
    orders.value = data
  } catch (e) {
    // Demo 数据
    orders.value = [
      { id: 'WO-001', device_id: 'PUMP-0007', fault_type: '轴承内圈磨损', severity: 'P1', assigned_engineer: '张三', status: 'in_progress', created_at: '2026-07-17T10:30:00' },
      { id: 'WO-002', device_id: 'PUMP-0042', fault_type: '不对中', severity: 'P2', assigned_engineer: '', status: 'pending', created_at: '2026-07-18T08:15:00' },
      { id: 'WO-003', device_id: 'PUMP-0015', fault_type: '密封泄漏', severity: 'P3', assigned_engineer: '李四', status: 'completed', created_at: '2026-07-16T14:00:00' },
    ]
  }
}

const assign = (row) => { row.assigned_engineer = '张三'; row.status = 'in_progress' }
const complete = (row) => { row.status = 'completed'; row.completed_at = new Date().toISOString() }
const showDetail = (row) => alert(JSON.stringify(row, null, 2))

onMounted(refresh)
</script>

<style scoped>
.workorders { padding: 16px; }
</style>
