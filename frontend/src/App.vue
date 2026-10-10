<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { fetchAlerts, removeAlert, upsertAlert } from './api'
import type { PriceAlert } from './types'

const alerts = ref<PriceAlert[]>([])
const status = ref('加载中…')
const newSymbol = ref('')
const newLevels = ref('')
const newLevelInput = reactive<Record<string, string>>({})
let timer: number | undefined

function normalizeSymbol(raw: string): string {
  let s = (raw || '').toUpperCase().replace(/[\s/_-]/g, '')
  if (!s.endsWith('USDT')) s += 'USDT'
  return s
}

function parseLevels(raw: string): number[] {
  const seen = new Set<number>()
  const out: number[] = []
  for (const t of (raw || '').split(/[,\s]+/)) {
    if (!t) continue
    const n = Number(t)
    if (Number.isFinite(n) && n > 0 && !seen.has(n)) {
      seen.add(n)
      out.push(n)
    }
  }
  return out.sort((a, b) => a - b)
}

function fmt(p: number | null): string {
  if (p === null || p === undefined) return '—'
  if (p >= 1000) return p.toFixed(2)
  if (p >= 1) return p.toFixed(4)
  return p.toFixed(6)
}

async function refresh() {
  try {
    const data = await fetchAlerts()
    alerts.value = data.alerts
    status.value = `数据源 ${data.source} · 最后刷新 ${new Date().toLocaleTimeString()}`
  } catch (e) {
    status.value = `刷新失败：${(e as Error).message}（后端是否已启动？）`
  }
}

async function add() {
  const symbol = normalizeSymbol(newSymbol.value)
  if (!symbol) {
    status.value = '请输入币种'
    return
  }
  await upsertAlert(symbol, parseLevels(newLevels.value), true)
  newSymbol.value = ''
  newLevels.value = ''
  await refresh()
}

async function toggle(a: PriceAlert) {
  await upsertAlert(a.symbol, a.levels, !a.enabled)
  await refresh()
}

async function removeSymbol(a: PriceAlert) {
  if (!confirm(`删除 ${a.symbol} 的所有提醒？`)) return
  await removeAlert(a.symbol)
  await refresh()
}

async function removeLevel(a: PriceAlert, level: number) {
  await upsertAlert(a.symbol, a.levels.filter((v) => v !== level), a.enabled)
  await refresh()
}

async function addLevel(a: PriceAlert, raw: string) {
  const nl = parseLevels(raw)
  if (!nl.length) return
  const merged = [...a.levels, ...nl].sort((x, y) => x - y)
  await upsertAlert(a.symbol, merged, a.enabled)
  newLevelInput[a.symbol] = ''
  await refresh()
}

onMounted(() => {
  refresh()
  timer = window.setInterval(refresh, 5000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <div class="wrap">
    <h1>🎯 点位提醒</h1>
    <p class="sub">设置币种与多个目标价位，价格向上突破或向下跌破时推送飞书卡片，提醒有冷却避免刷屏。</p>

    <div class="bar">
      <input v-model="newSymbol" class="sym-input" placeholder="币种，如 PYTH / ASTER" @keyup.enter="add" />
      <input v-model="newLevels" class="levels-input" placeholder="价位，逗号或空格分隔，如 0.88 1 1.25" @keyup.enter="add" />
      <button @click="add">添加监控</button>
    </div>

    <div v-if="!alerts.length" class="empty">还没有监控项，先在上方添加币种和价位。</div>

    <div v-for="a in alerts" :key="a.symbol" class="card">
      <div class="card-head">
        <span class="sym">{{ a.symbol }}</span>
        <label class="switch">
          <input type="checkbox" :checked="a.enabled" @change="toggle(a)" />
          <span>启用</span>
        </label>
        <button class="danger" @click="removeSymbol(a)">删除</button>
      </div>

      <div class="price">当前价格 <b>{{ fmt(a.last_price) }}</b> USDT</div>

      <div class="levels">
        <span v-for="lv in a.levels" :key="lv" class="chip">
          <span>{{ lv }}</span>
          <button title="删除该价位" @click="removeLevel(a, lv)">×</button>
        </span>
        <span v-if="!a.levels.length" class="hint">还没有价位，下方添加</span>
      </div>

      <div class="add-level">
        <input
          v-model="newLevelInput[a.symbol]"
          :placeholder="'新价位，如 1.25'"
          @keyup.enter="addLevel(a, newLevelInput[a.symbol])"
        />
        <button @click="addLevel(a, newLevelInput[a.symbol])">加价位</button>
      </div>
    </div>

    <div class="status">{{ status }}</div>
  </div>
</template>
