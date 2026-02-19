async function tryFetchAny(paths) {
    for (const p of paths) {
        try {
            const r = await fetch(p, {cache: "no-store"});
            if (r.ok) return await r.json();
        } catch (e) {}
    }
    return null;
}

(async function() {
    const preferPaths = [
        'author_counts.json',
        '/stats/author_counts.json'
    ];

    const data = await tryFetchAny(preferPaths);

    const noDataEl = document.getElementById('no-data');
    if (!data || !data.raw || !Array.isArray(data.raw) || data.raw.length === 0) {
        noDataEl.style.display = 'block';
        return;
    } else {
        noDataEl.style.display = 'none';
    }

    const raw = data.raw.slice();

    // Controls
    const topNSlider = document.getElementById('topN');
    const topNValue = document.getElementById('topNvalue');
    const tbody = document.getElementById('authors-body');

    topNSlider.addEventListener('input', () => {
        topNValue.textContent = topNSlider.value;
        updateChartAndTable();
    });

    // Chart
    let chart = null;
    const ctx = document.getElementById('authorsChart').getContext('2d');

    function buildDatasets(list) {
        const labels = list.map(d => d.author);
        const values = list.map(d => d.count);
        return { labels, values, raw: list };
    }

    function renderTable(list) {
        tbody.innerHTML = '';
        for (const r of list) {
            const tr = document.createElement('tr');
            const a = document.createElement('td');
            a.textContent = r.author;
            const b = document.createElement('td');
            b.textContent = r.count;
            tr.appendChild(a);
            tr.appendChild(b);
            tbody.appendChild(tr);
        }
    }

    function renderChart(list) {
        const ds = buildDatasets(list);

        if (chart) chart.destroy();

        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ds.labels,
                datasets: [{
                    label: 'Poems',
                    data: ds.values,
                    borderWidth: 1,
                    hoverBorderWidth: 2
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (items) => items[0].label,
                            label: (ctx) => `${ctx.formattedValue} poem${ctx.raw === 1 ? '' : 's'}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { autoSkip: false, maxRotation: 45, minRotation: 0 },
                        title: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        precision: 0,
                        ticks: { stepSize: 1 }
                    }
                },
                onClick: (evt, elements) => {
                    if (!elements.length) return;
                    const idx = elements[0].index;
                    const row = ds.raw[idx];
                }
            }
        });
    }

    function updateChartAndTable() {
        const N = parseInt(topNSlider.value, 10) || 10;
        const sorted = raw.slice().sort((a,b) => b.count - a.count || a.author.localeCompare(b.author));
        const top = sorted.slice(0,N);
        renderChart(top);
        renderTable(top);
    }

    topNSlider.max = Math.max(5, raw.length);
    topNSlider.value = Math.min(10, raw.length);
    topNValue.textContent = topNSlider.value;
    
    // render
    updateChartAndTable();
 })();