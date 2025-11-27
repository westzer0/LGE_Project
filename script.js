const slider = document.querySelector('.slider');
const slides = Array.from(document.querySelectorAll('.slide'));
const dotsContainer = document.querySelector('.dots');
const prevBtn = document.querySelector('.slider__control.prev');
const nextBtn = document.querySelector('.slider__control.next');

const timeDealCards = document.querySelector('#timeDealCards');
const mdChoiceGrid = document.querySelector('#mdChoiceGrid');

const timeDeals = [
    {
        badge: '타임딜',
        title: 'LG 올레드 evo C4 (48형)',
        desc: '모델명 OLED48C4ENA · 스탠드형',
        price: '최대혜택가 1,181,100원',
        stock: 'D-3 · 14개 남음',
    },
    {
        badge: '타임딜',
        title: 'LG 올레드 evo C4 (42형)',
        desc: '모델명 OLED42C4ENA · 스탠드형',
        price: '최대혜택가 1,060,200원',
        stock: 'D-3 · 20개 남음',
    },
    {
        badge: '타임딜',
        title: 'LG 울트라 HD TV (75형)',
        desc: '모델명 75UT9300BNA · 벽걸이형',
        price: '최대혜택가 1,218,300원',
        stock: 'D-3 · 116개 남음 · 닷컴 ONLY',
    },
    {
        badge: '타임딜',
        title: 'LG 나노셀 AI (65형)',
        desc: '모델명 65NANO80AEA · 스탠드형',
        price: '최대혜택가 1,004,400원',
        stock: 'D-3 · 52개 남음 · 닷컴 ONLY',
    },
];

const mdChoice = [
    {
        badge: 'MD Pick',
        title: 'LG 퓨리케어 오브제컬렉션 하이드로에센셜',
        desc: 'HY505RWLAHM · 무빙휠 세트',
        price: '947,700원',
    },
    {
        badge: 'MD Pick',
        title: 'LG 트롬 워시타워 23/20kg',
        desc: 'W20WAN · 에너지 1등급',
        price: '1,990,200원',
    },
    {
        badge: 'MD Pick',
        title: 'LG 퓨리케어 360˚ 공기청정기',
        desc: 'AS183HWWA · 62㎡ 커버리지',
        price: '369,000원',
    },
    {
        badge: 'MD Pick',
        title: 'LG 울트라기어 올레드 게이밍모니터',
        desc: '27GX704A · 67.3cm',
        price: '715,200원',
    },
    {
        badge: 'MD Pick',
        title: 'LG 디오스 오브제컬렉션 식기세척기',
        desc: 'DUE4BGE · 스팀 · 1등급',
        price: '780,300원',
    },
    {
        badge: 'MD Pick',
        title: 'LG 스탠바이미 2',
        desc: '27LX6TPGA · 이동형 스크린',
        price: '1,134,600원',
    },
];

let current = 0;
let timer;

const createDots = () => {
    slides.forEach((_, index) => {
        const dot = document.createElement('button');
        dot.type = 'button';
        dot.setAttribute('aria-label', `${index + 1}번 슬라이드로 이동`);
        dot.addEventListener('click', () => goToSlide(index));
        dotsContainer.appendChild(dot);
    });
};

const updateActive = () => {
    slides.forEach((slide, index) => {
        slide.classList.toggle('active', index === current);
    });
    Array.from(dotsContainer.children).forEach((dot, index) => {
        dot.classList.toggle('active', index === current);
    });
};

const goToSlide = (index) => {
    current = (index + slides.length) % slides.length;
    updateActive();
    resetTimer();
};

const nextSlide = () => goToSlide(current + 1);
const prevSlide = () => goToSlide(current - 1);

const startAutoplay = () => {
    timer = setInterval(nextSlide, 6000);
};

const resetTimer = () => {
    clearInterval(timer);
    startAutoplay();
};

const renderDeals = () => {
    timeDeals.forEach((deal) => {
        const card = document.createElement('article');
        card.className = 'deal-card';
        card.innerHTML = `
      <span class="badge">${deal.badge}</span>
      <h3>${deal.title}</h3>
      <p>${deal.desc}</p>
      <strong>${deal.price}</strong>
      <small class="muted">${deal.stock}</small>
    `;
        timeDealCards.appendChild(card);
    });
};

const renderMdChoice = () => {
    mdChoice.forEach((item) => {
        const card = document.createElement('article');
        card.className = 'product-card';
        card.innerHTML = `
      <span class="badge">${item.badge}</span>
      <h3>${item.title}</h3>
      <p>${item.desc}</p>
      <strong>${item.price}</strong>
      <button class="ghost" type="button">자세히 보기</button>
    `;
        mdChoiceGrid.appendChild(card);
    });
};

createDots();
updateActive();
startAutoplay();
renderDeals();
renderMdChoice();

nextBtn.addEventListener('click', nextSlide);
prevBtn.addEventListener('click', prevSlide);

slider.addEventListener('mouseenter', () => clearInterval(timer));
slider.addEventListener('mouseleave', startAutoplay);

