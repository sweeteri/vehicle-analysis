document.addEventListener('DOMContentLoaded', function() {
    // Обработчики для формы симуляции
    const form = document.getElementById('vehicle_simulation-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Валидация формы перед отправкой
            const startDate = new Date(document.getElementById('start_date').value);
            const endDate = new Date(document.getElementById('end_date').value);

            if (startDate >= endDate) {
                alert('Дата окончания должна быть позже даты начала');
                e.preventDefault();
            }
        });
    }

    // Инициализация графиков, если есть данные
    if (typeof plotData !== 'undefined') {
        initializeCharts(plotData);
    }
});