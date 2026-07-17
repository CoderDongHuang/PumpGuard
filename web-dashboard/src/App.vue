<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h1>PumpGuard 数字孪生看板</h1>
        <div class="header-stats">
          <span class="stat healthy">健康 {{ stats.healthy_pumps || 0 }}</span>
          <span class="stat warning">告警 {{ stats.warning_pumps || 0 }}</span>
          <span class="stat total">总计 {{ stats.total_pumps || 0 }}</span>
        </div>
      </el-header>
      <el-main>
        <router-view :stats="stats" />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const stats = ref({ total_pumps: 0, healthy_pumps: 0, warning_pumps: 0, health_rate: 100 })
let timer = null

const fetchStats = async () => {
  try {
    const { data } = await axios.get('/api/stats/global')
    stats.value = data
  } catch (e) {
    console.warn('获取统计失败，后端未启动')
  }
}

onMounted(() => {
  fetchStats()
  timer = setInterval(fetchStats, 10000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, -apple-system, sans-serif; background: #f5f5f5; }

.app-header {
  background: #2a78d6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
}

.app-header h1 { font-size: 18px; font-weight: 600; }

.header-stats .stat {
  margin-left: 16px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
}
.stat.healthy { background: rgba(255,255,255,0.2); }
.stat.warning { background: #eb6834; }
.stat.total { background: rgba(255,255,255,0.15); }
</style>
