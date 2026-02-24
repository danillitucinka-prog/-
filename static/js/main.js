// Основной JS файл

document.addEventListener('DOMContentLoaded', function() {
    // Закрытие алертов
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    alertCloseButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Автозакрытие алертов через 5 секунд
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('permanent')) {
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
    });
});

// AJAX голосование за посты
function votePost(postId, voteType) {
    const url = `/post/${postId}/${voteType}`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Обновить счетчики
        updateVoteCounts(postId, data);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при голосовании');
    });
}

// AJAX голосование за комментарии
function voteComment(commentId, voteType) {
    const url = `/comment/${commentId}/${voteType}`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Обновить счетчики
        updateVoteCounts(commentId, data);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при голосовании');
    });
}

function updateVoteCounts(id, data) {
    // Найти элемент с ID и обновить его
    const element = document.querySelector(`[data-id="${id}"]`);
    if (element) {
        element.querySelector('.upvotes').textContent = data.upvotes;
        element.querySelector('.downvotes').textContent = data.downvotes;
    }
}

// Копирование ссылки на пост
function sharePost(postId) {
    fetch(`/post/${postId}/share`)
        .then(response => response.json())
        .then(data => {
            // Копировать в буфер обмена
            navigator.clipboard.writeText(data.link).then(() => {
                alert('Ссылка скопирована в буфер обмена!');
            });
        });
}

// Переключение темы
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Загрузка сохраненной темы
window.addEventListener('load', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
});
