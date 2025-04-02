// Theme management
const themeToggleBtn = document.getElementById('themeToggle');
const htmlElement = document.documentElement;
const DARK_THEME = 'dark';
const LIGHT_THEME = 'light';
const THEME_KEY = 'preferred-theme';

// Function to set theme
function setTheme(theme) {
    htmlElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    
    // Update button icon
    const icon = themeToggleBtn.querySelector('i');
    icon.className = theme === DARK_THEME ? 'fas fa-sun' : 'fas fa-moon';
}

// Initialize theme
function initTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY) || LIGHT_THEME;
    setTheme(savedTheme);
}

// Toggle theme
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
        setTheme(newTheme);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initTheme);
