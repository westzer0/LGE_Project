const slider = document.querySelector('.slider');
const slides = Array.from(document.querySelectorAll('.slide'));
const dotsContainer = document.querySelector('.dots');
const prevBtn = document.querySelector('.slider__control.prev');
const nextBtn = document.querySelector('.slider__control.next');

let current = 0;
let timer;

function createDots() {
  slides.forEach((_, index) => {
    const dot = document.createElement('button');
    dot.setAttribute('aria-label', `${index + 1}번 슬라이드로 이동`);
    dot.addEventListener('click', () => goToSlide(index));
    dotsContainer.appendChild(dot);
  });
}

function updateActive() {
  slides.forEach((slide, index) => {
    slide.classList.toggle('active', index === current);
  });
  Array.from(dotsContainer.children).forEach((dot, index) => {
    dot.classList.toggle('active', index === current);
  });
}

function goToSlide(index) {
  current = (index + slides.length) % slides.length;
  updateActive();
  resetTimer();
}

function nextSlide() {
  goToSlide(current + 1);
}

function prevSlide() {
  goToSlide(current - 1);
}

function startAutoplay() {
  timer = setInterval(nextSlide, 5000);
}

function resetTimer() {
  clearInterval(timer);
  startAutoplay();
}

createDots();
updateActive();
startAutoplay();

nextBtn.addEventListener('click', nextSlide);
prevBtn.addEventListener('click', prevSlide);

slider.addEventListener('mouseenter', () => clearInterval(timer));
slider.addEventListener('mouseleave', startAutoplay);

