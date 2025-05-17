document.addEventListener('DOMContentLoaded', function () {
    // Переключение между типами анализа
    const analysisTypeRadios = document.querySelectorAll('input[name="analysis_type"]');
    const singleAnalysisDiv = document.getElementById('single-analysis');
    const typeComparisonDiv = document.getElementById('type-comparison');

    function toggleAnalysisType() {
        const selectedValue = document.querySelector('input[name="analysis_type"]:checked').value;
        singleAnalysisDiv.style.display = selectedValue === 'single' ? 'block' : 'none';
        typeComparisonDiv.style.display = selectedValue === 'type_avg' ? 'block' : 'none';
    }

    analysisTypeRadios.forEach(radio => {
        radio.addEventListener('change', toggleAnalysisType);
    });

    // Инициализация при загрузке
    toggleAnalysisType();

    // Валидация формы
    const form = document.querySelector('.needs-validation');
    form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    }, false);
});