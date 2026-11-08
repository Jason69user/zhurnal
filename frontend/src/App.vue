<template>
  <div class="app">
    <header>
      <h1>📔 Журнал</h1>
      <p class="subtitle">Траты и идеи в одном месте</p>
    </header>

    <div class="input-block">
      <input
        v-model="text"
        placeholder="потратил 500 на еду или идея: сделать проект #devops"
        @keyup.enter="addEntry"
      />
      <button @click="addEntry">Добавить</button>
    </div>

    <p v-if="message" class="message">{{ message }}</p>

    <div class="stats">
      <div class="stat-card">
        <span class="stat-label">Сегодня</span>
        <span class="stat-value">{{ todayTotal }} ₽</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Всего записей</span>
        <span class="stat-value">{{ expenses.length + notes.length }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Категорий</span>
        <span class="stat-value">{{ uniqueCategories }}</span>
      </div>
    </div>

    <div class="controls">
      <input
        v-model="searchQuery"
        placeholder="🔍 Поиск..."
        class="search-input"
      />
      <select v-model="sortOrder" class="sort-select">
        <option value="new">Сначала новые</option>
        <option value="old">Сначала старые</option>
      </select>
    </div>

    <div class="columns">
      <section class="column">
        <h2>💰 Траты ({{ filteredExpenses.length }})</h2>

        <div class="category-filter">
          <button
            v-for="cat in categories"
            :key="cat"
            :class="{ active: selectedCategory === cat }"
            @click="selectedCategory = cat"
            class="filter-btn"
          >
            {{ cat }}
          </button>
        </div>

        <div v-if="filteredExpenses.length === 0" class="empty">Пока пусто</div>
        <div v-for="expense in filteredExpenses" :key="expense.id" class="card expense-card">
          <div class="card-header">
            <span class="amount">{{ expense.amount }} ₽</span>
            <div class="card-actions">
              <span class="category">{{ expense.category }}</span>
              <button @click="deleteExpense(expense.id)" class="delete-btn">✕</button>
            </div>
          </div>
          <p class="raw-text">{{ expense.raw_text }}</p>
          <span class="date">{{ formatDate(expense.created_at) }}</span>
        </div>
      </section>

      <section class="column">
        <h2>💡 Идеи ({{ filteredNotes.length }})</h2>

        <div v-if="filteredNotes.length === 0" class="empty">Пока пусто</div>
        <div v-for="note in filteredNotes" :key="note.id" class="card note-card">
          <div class="card-header">
            <p class="note-content">{{ note.content }}</p>
            <button @click="deleteNote(note.id)" class="delete-btn">✕</button>
          </div>
          <div v-if="note.tags && note.tags.length" class="tags">
            <span v-for="tag in note.tags" :key="tag" class="tag">#{{ tag }}</span>
          </div>
          <span class="date">{{ formatDate(note.created_at) }}</span>
        </div>
      </section>
    </div>
    <Calendar />
  </div>
</template>


<script setup>
import { ref, computed } from 'vue'
import Calendar from './components/Calendar.vue'

const text = ref('')
const message = ref('')
const expenses = ref([])
const notes = ref([])
const searchQuery = ref('')
const sortOrder = ref('new')
const selectedCategory = ref('все')

const categories = computed(() => {
  const cats = new Set(expenses.value.map(e => e.category))
  return ['все', ...Array.from(cats)]
})

const filteredExpenses = computed(() => {
  let result = expenses.value

  // Фильтр по категории
  if (selectedCategory.value !== 'все') {
    result = result.filter(e => e.category === selectedCategory.value)
  }

  // Поиск
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(e => e.raw_text.toLowerCase().includes(query))
  }

  // Сортировка
  result = [...result]
  if (sortOrder.value === 'new') {
    result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } else {
    result.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  }

  return result
})

const filteredNotes = computed(() => {
  let result = notes.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(n => n.raw_text.toLowerCase().includes(query))
  }

  result = [...result]
  if (sortOrder.value === 'new') {
    result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } else {
    result.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
  }

  return result
})

const todayTotal = computed(() => {
  const now = new Date()
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  return expenses.value
    .filter(e => e.created_at.startsWith(today))
    .reduce((sum, e) => sum + e.amount, 0)
    .toFixed(2)
})

const uniqueCategories = computed(() => {
  return new Set(expenses.value.map(e => e.category)).size
})

function formatDate(isoDate) {
  const date = new Date(isoDate)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function addEntry() {
  if (!text.value) return

  try {
    const response = await fetch('/api/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text.value })
    })

    const data = await response.json()

    if (data.status === 'ok') {
      message.value = `✅ Добавлено: ${data.type === 'expense' ? 'трата' : 'заметка'}`
      text.value = ''
      await loadAll()
    } else {
      message.value = `⚠️ ${data.message || 'Не удалось распознать'}`
    }

    setTimeout(() => { message.value = '' }, 3000)
  } catch (error) {
    message.value = `❌ Ошибка: ${error.message}`
  }
}

async function deleteExpense(id) {
  if (!confirm('Удалить трату?')) return
  await fetch(`/api/expenses/${id}`, { method: 'DELETE' })
  await loadAll()
}

async function deleteNote(id) {
  if (!confirm('Удалить заметку?')) return
  await fetch(`/api/notes/${id}`, { method: 'DELETE' })
  await loadAll()
}

async function loadAll() {
  const [expensesRes, notesRes] = await Promise.all([
    fetch('/api/expenses'),
    fetch('/api/notes')
  ])
  expenses.value = await expensesRes.json()
  notes.value = await notesRes.json()
}

loadAll()
</script>

<style>
* { box-sizing: border-box; }

body {
  margin: 0;
  background: #0f0f1a;
  color: #e5e5e5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app { max-width: 1000px; margin: 0 auto; padding: 20px; }

header { text-align: center; margin-bottom: 30px; }
h1 { margin: 0; font-size: 32px; color: #fff; }
.subtitle { margin: 5px 0 0; color: #888; font-size: 14px; }

.input-block { display: flex; gap: 10px; margin-bottom: 20px; }

input, select {
  padding: 14px 18px;
  font-size: 16px;
  border: 2px solid #2a2a3e;
  border-radius: 12px;
  background: #1a1a2e;
  color: #fff;
  outline: none;
  transition: border-color 0.2s;
}

input:focus, select:focus { border-color: #6366f1; }

input { flex: 1; }

button {
  padding: 14px 28px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  background: #6366f1;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover { background: #4f46e5; }

.message {
  padding: 12px;
  border-radius: 8px;
  background: #1a1a2e;
  text-align: center;
  margin-bottom: 20px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: #1a1a2e;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid #2a2a3e;
}

.stat-label {
  color: #888;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value { font-size: 24px; font-weight: 700; color: #fff; }

.controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.search-input { flex: 1; }
.sort-select { min-width: 180px; }

.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 15px;
}

.filter-btn {
  padding: 6px 12px;
  font-size: 13px;
  background: #1a1a2e;
  border: 1px solid #2a2a3e;
  border-radius: 20px;
  color: #aaa;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover { border-color: #6366f1; color: #fff; }

.filter-btn.active {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}

.columns { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

@media (max-width: 768px) {
  .columns { grid-template-columns: 1fr; }
  .stats { grid-template-columns: 1fr; }
}

.column h2 { font-size: 18px; margin-bottom: 15px; color: #ccc; }

.empty {
  text-align: center;
  color: #555;
  padding: 40px;
  font-style: italic;
}

.card {
  background: #1a1a2e;
  padding: 15px;
  border-radius: 12px;
  margin-bottom: 12px;
  border-left: 4px solid #6366f1;
  transition: transform 0.2s;
}

.card:hover { transform: translateX(4px); }
.expense-card { border-left-color: #ef4444; }
.note-card { border-left-color: #10b981; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 10px;
}

.card-actions { display: flex; align-items: center; gap: 8px; }

.amount { font-size: 20px; font-weight: 700; color: #ef4444; }

.category {
  font-size: 12px;
  background: #2a2a3e;
  padding: 4px 10px;
  border-radius: 20px;
  color: #aaa;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 16px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.delete-btn:hover { background: #ef444433; color: #ef4444; }

.raw-text { margin: 8px 0; color: #ccc; font-size: 14px; }
.note-content { margin: 0; color: #e5e5e5; font-size: 15px; flex: 1; }

.tags { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0; }

.tag {
  font-size: 12px;
  background: #10b98133;
  color: #10b981;
  padding: 3px 8px;
  border-radius: 20px;
}

.date { display: block; font-size: 11px; color: #666; margin-top: 8px; }
</style>