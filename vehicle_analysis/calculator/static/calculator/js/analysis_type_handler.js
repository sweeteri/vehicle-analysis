// Переключение между режимами анализа
document.querySelectorAll('input[name="analysis_type"]').forEach(radio => {
    radio.addEventListener('change', function () {
        document.getElementById('single-analysis').style.display =
            this.value === 'single' ? 'block' : 'none';
        document.getElementById('type-comparison').style.display =
            this.value === 'type_avg' ? 'block' : 'none';
    });
});
