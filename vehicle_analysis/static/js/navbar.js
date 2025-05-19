document.addEventListener('DOMContentLoaded', function() {
    // Функция для активации текущей вкладки
    function activateCurrentNavItem() {
        const currentUrl = window.location.pathname;
        const navLinks = document.querySelectorAll('#mainNav .nav-link');

        navLinks.forEach(link => {
            const linkUrl = new URL(link.href).pathname;

            // Нормализуем URL, удаляя слеши в конце для сравнения
            const normalizeUrl = url => url.endsWith('/') ? url.slice(0, -1) : url;

            if (normalizeUrl(currentUrl) === normalizeUrl(linkUrl)) {
                link.classList.add('active');
            }
        });
    }

    // Вызываем функцию при загрузке страницы
    activateCurrentNavItem();

    // Можно также вызвать при изменении истории (если используете AJAX)
    window.addEventListener('popstate', activateCurrentNavItem);
});