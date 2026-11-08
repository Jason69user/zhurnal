<template>
  <div class="calendar">
    <div class="calendar-header">
      <button @click="prevMonth">←</button>
      <h2>{{ monthName }} {{ currentYear }}</h2>
      <button @click="nextMonth">→</button>
    </div>

    <div class="weekdays">
      <div v-for="day in weekdays" :key="day">{{ day }}</div>
    </div>

    <div class="days-grid">
      <div
        v-for="day in daysInMonth"
        :key="day.date"
        class="day-cell"
        :class="{ 'other-month': !day.isCurrentMonth, today: day.isToday }"
        @click="selectDay(day)"
      >
        <span class="day-number">{{ day.dayNumber }}</span>
        <div v-if="day.events.length" class="events">
          <div
            v-for="event in day.events"
            :key="event.id"
            class="event-line"
          >
            {{ event.title }}
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно дня -->
    <div v-if="selectedDay" class="modal-overlay" @click.self="selectedDay = null">
      <div class="modal">
        <h3>{{ selectedDay.date }}</h3>
        <div v-if="selectedDay.events.length === 0" class="empty">Нет событий</div>
        <div v-for="event in selectedDay.events" :key="event.id" class="event-card">
          <span class="event-time">{{ formatTime(event.event_date) }}</span>
          <span class="event-title">{{ event.title }}</span>
          <button @click="deleteEvent(event.id)" class="delete-btn">✕</button>
        </div>
        <button @click="selectedDay = null" class="close-btn">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const events = ref([])
const currentDate = ref(new Date())
const selectedDay = ref(null)

const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const monthName = computed(() => {
  const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
  return months[currentDate.value.getMonth()]
})

const currentYear = computed(() => currentDate.value.getFullYear())

const daysInMonth = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // Сдвиг: понедельник = 0
  let startOffset = firstDay.getDay() - 1
  if (startOffset < 0) startOffset = 6

  const days = []

  // Дни предыдущего месяца
  for (let i = startOffset - 1; i >= 0; i--) {
    const date = new Date(year, month, -i)
    days.push(makeDay(date, false))
  }

  // Дни текущего месяца
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month, i)
    days.push(makeDay(date, true))
  }

  // Дни следующего месяца (до 42 ячеек)
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const date = new Date(year, month + 1, i)
    days.push(makeDay(date, false))
  }

  return days
})

function toLocalDateStr(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function makeDay(date, isCurrentMonth) {
  const dateStr = toLocalDateStr(date)
  const today = toLocalDateStr(new Date())

  return {
    date: dateStr,
    dayNumber: date.getDate(),
    isCurrentMonth,
    isToday: dateStr === today,
    events: events.value.filter(e => e.event_date.startsWith(dateStr))
  }
}

function formatTime(isoDate) {
  const date = new Date(isoDate)
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function prevMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1, 1)
}

function nextMonth() {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1, 1)
}

function selectDay(day) {
  selectedDay.value = day
}

async function deleteEvent(id) {
  if (!confirm('Удалить событие?')) return
  await fetch(`/api/events/${id}`, { method: 'DELETE' })
  await loadEvents()
  selectedDay.value = null
}

async function loadEvents() {
  const response = await fetch('/api/events')
  events.value = await response.json()
}

onMounted(loadEvents)
</script>

<style scoped>
.calendar {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #2a2a3e;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.calendar-header h2 {
  margin: 0;
  color: #fff;
  font-size: 20px;
}

.calendar-header button {
  background: #2a2a3e;
  color: #fff;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s;
}

.calendar-header button:hover {
  background: #6366f1;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.weekdays div {
  text-align: center;
  color: #888;
  font-size: 12px;
  padding: 8px 0;
  font-weight: 600;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-cell {
  min-height: 80px;
  padding: 6px;
  background: #0f0f1a;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  border: 1px solid transparent;
}

.day-cell:hover {
  background: #2a2a3e;
  border-color: #6366f1;
}

.day-cell.other-month {
  opacity: 0.3;
}

.day-cell.today {
  border-color: #6366f1;
  background: #1a1a3e;
}

.day-number {
  font-size: 13px;
  color: #ccc;
  font-weight: 600;
}

.events {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-line {
  font-size: 10px;
  background: #6366f1;
  color: #fff;
  padding: 2px 4px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: #1a1a2e;
  padding: 25px;
  border-radius: 12px;
  min-width: 400px;
  max-width: 500px;
  border: 1px solid #2a2a3e;
}

.modal h3 {
  margin-top: 0;
  color: #fff;
}

.event-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #0f0f1a;
  border-radius: 8px;
  margin-bottom: 8px;
  border-left: 3px solid #6366f1;
}

.event-time {
  color: #6366f1;
  font-weight: 600;
  font-size: 13px;
}

.event-title {
  flex: 1;
  color: #e5e5e5;
}

.empty {
  text-align: center;
  color: #666;
  padding: 20px;
}

.close-btn {
  width: 100%;
  padding: 10px;
  background: #2a2a3e;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 10px;
}

.close-btn:hover {
  background: #6366f1;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px 8px;
}

.delete-btn:hover {
  color: #ef4444;
}
</style>