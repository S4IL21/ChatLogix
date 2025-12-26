async function getMembers() {
  const res = await fetch('/api/members');
  if (!res.ok) return [];
  return await res.json();
}

async function getStats(username) {
  const res = await fetch('/api/fetch-stats', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username})
  });
  return res.ok ? res.json() : null;
}

async function getOverallActivity(username) {
  const res = await fetch('/api/overall-activity', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username})
  });
  return res.ok ? res.json() : null;
}

async function getTopMembers() {
  const res = await fetch('/api/top-active-members');
  return res.ok ? res.json() : null;
}

function renderActivityChart(data) {
  const ctx = document.getElementById('activity-chart').getContext('2d');
  const labels = data.map(d => d.Date);
  const values = data.map(d => d.Message);
  if (window.activityChart) window.activityChart.destroy();
  window.activityChart = new Chart(ctx, {
    type: 'line', data: {labels, datasets: [{label: 'Messages', data: values, borderColor: '#4F46E5', tension: 0.2}]}, options: {responsive: true}
  });
}

function renderTopMembers(data) {
  const ctx = document.getElementById('top-members-chart').getContext('2d');
  const labels = data.map(d => d.User);
  const values = data.map(d => d.Message);
  if (window.topChart) window.topChart.destroy();
  window.topChart = new Chart(ctx, {
    type: 'bar', data: {labels, datasets: [{label: 'Messages', data: values, backgroundColor: '#06b6d4'}]}, options: {responsive: true}
  });
}

async function init() {
  const members = await getMembers();
  const select = document.getElementById('member-select');
  select.innerHTML = '';
  members.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.username;
    opt.textContent = m.username;
    select.appendChild(opt);
  });

  // initial load: Overall Group
  const initial = 'Overall Group';
  select.value = initial;
  await loadForUser(initial);

  select.addEventListener('change', async (e) => {
    await loadForUser(e.target.value);
  });

  // load top members chart
  const top = await getTopMembers();
  if (top) renderTopMembers(top.slice(0, 8));
}

async function loadForUser(username) {
  const stats = await getStats(username);
  if (stats) {
    document.getElementById('card-messages').textContent = `Total Messages: ${stats['Total Messages'] ?? '—'}`;
    document.getElementById('card-words').textContent = `Total Words: ${stats['Total Words'] ?? '—'}`;
    document.getElementById('card-media').textContent = `Media Shared: ${stats['Media Shared'] ?? '—'}`;
  }
  const activity = await getOverallActivity(username);
  if (activity) renderActivityChart(activity.slice(-30)); // last 30 days
}

window.addEventListener('load', init);
