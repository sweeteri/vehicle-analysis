function initializeCharts(plotData, index) {
    // График стоимости
    new Chart(document.getElementById(`costChart`), {
        type: 'line',
        data: {
            labels: plotData.dates,
            datasets: [{
                label: 'Накопленная стоимость (руб)',
                data: plotData.total_cost,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика стоимости владения'
                }
            }
        }
    });

    // График выбросов
    new Chart(document.getElementById(`emissionsChart`), {
        type: 'line',
        data: {
            labels: plotData.dates,
            datasets: [{
                label: 'Накопленные выбросы CO₂ (г)',
                data: plotData.total_emissions,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика выбросов CO₂'
                }
            }
        }
    });

    // График энергопотребления
    new Chart(document.getElementById(`energyChart`), {
        type: 'line',
        data: {
            labels: plotData.dates,
            datasets: [{
                label: 'Накопленное энергопотребление (МДж)',
                data: plotData.total_energy,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика энергопотребления'
                }
            }
        }
    });

    // График средних дневных показателей
    new Chart(document.getElementById(`dailyChart`), {
        type: 'bar',
        data: {
            labels: ['Стоимость', 'Выбросы', 'Энергия'],
            datasets: [{
                label: 'Средние дневные показатели',
                data: [
                    plotData.daily_cost.reduce((a, b) => a + b, 0) / plotData.daily_cost.length,
                    plotData.daily_emissions.reduce((a, b) => a + b, 0) / plotData.daily_emissions.length,
                    plotData.daily_energy.reduce((a, b) => a + b, 0) / plotData.daily_energy.length
                ],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(54, 162, 235, 0.6)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Средние дневные показатели'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}