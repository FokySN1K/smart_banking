// confirmation.js - Скрипт для обработки подтверждений

// Основная функция подтверждения
function showConfirmation(message = "Вы уверены, что хотите выполнить это действие?") {
    return confirm(message);
}

// Функция для логирования действий
function logAction(action, confirmed) {
    const logList = document.getElementById('logList');
    const timestamp = new Date().toLocaleTimeString();
    
    const logItem = document.createElement('li');
    
    if (confirmed) {
        logItem.textContent = `✅ [${timestamp}] ${action} - ВЫПОЛНЕНО`;
        logItem.classList.add('confirmed');
    } else {
        logItem.textContent = `❌ [${timestamp}] ${action} - ОТМЕНЕНО`;
        logItem.classList.add('cancelled');
    }
    
    logList.appendChild(logItem);
    
    // Автопрокрутка к последнему действию
    logItem.scrollIntoView({ behavior: 'smooth' });
}

// Функция для удаления файла
function handleDeleteCard() {
    const confirmed = showConfirmation("Вы уверены, что хотите удалить файл? Это действие нельзя отменить.");
    
    if (confirmed) {
        // Здесь код для удаления файла
        url_for('delete_card', card_id=item['card_id'])
    } else {
        logAction("Удаление файла", false);
    }
}


// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("Скрипт confirmation.js загружен и готов к работе!");
    
    // Назначаем обработчики событий кнопкам
    const deleteBtn = document.getElementById('deleteBtn');
    const saveBtn = document.getElementById('saveBtn');
    const publishBtn = document.getElementById('publishBtn');
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', handleDelete);
    }
    
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSave);
    }
    
    if (publishBtn) {
        publishBtn.addEventListener('click', handlePublish);
    }
    
    // Добавляем сообщение в лог при загрузке
    logAction("Страница загружена", true);
});

// Дополнительные утилиты (можно вынести в отдельный файл)
const ConfirmationUtils = {
    // Подтверждение с кастомным текстом
    customConfirm: function(message, confirmText = "Да", cancelText = "Нет") {
        // Здесь можно реализовать кастомное модальное окно
        return confirm(message);
    },
    
    // Очистка лога
    clearLog: function() {
        const logList = document.getElementById('logList');
        if (logList && confirm("Очистить историю действий?")) {
            logList.innerHTML = '';
            logAction("История действий очищена", true);
        }
    }
};

// Добавляем глобальную функцию для очистки лога (для тестирования)
window.clearActionLog = ConfirmationUtils.clearLog;