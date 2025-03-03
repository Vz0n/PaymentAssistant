const TRANSITION_DURATION = 500;

var isInTrasition = false;
var currentBg = parseInt(sessionStorage.getItem('currentBg') || '1');
var backgrounds = {
    bg1: document.querySelector('.background-container .bg-1'),
    bg2: document.querySelector('.background-container .bg-2'),
    bg3: document.querySelector('.background-container .bg-3')
};

async function switchBackground() {
    if (isInTrasition) return;
    isInTrasition = true;
   
    let nextBg = (currentBg % 3) + 1;

    // Update opacities
    backgrounds[`bg${currentBg}`].style.opacity = '0';
    backgrounds[`bg${nextBg}`].style.opacity = '1';

    console.log(backgrounds);

    // Store state
    currentBg = nextBg;
    sessionStorage.setItem('currentBg', currentBg);

    // Reset transition lock
    setTimeout(() => {
        isInTrasition = false;
    }, TRANSITION_DURATION);
}

function initBackgroundSwitcher() {
    const switcher = document.getElementById('theme-switcher');
    let initialStyle = document.createElement('style');

    initialStyle.textContent = `
       .background-container .hero-bg {
          transition: opacity ${TRANSITION_DURATION}ms ease-in-out;
          opacity: 0;
        }
    `;
    document.head.appendChild(initialStyle);
    backgrounds[`bg${currentBg}`].style.opacity = '1';

    setInterval(switchBackground, 10000);

    // Manual switching with debounce
    if (switcher) {
        switcher.addEventListener('click', () => {
            switchBackground();
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBackgroundSwitcher);
} 