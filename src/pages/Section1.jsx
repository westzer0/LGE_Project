import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const Section1 = () => {
  const navigate = useNavigate()
  const [currentSlide, setCurrentSlide] = useState(0)
  const sliderRef = useRef(null)
  const timerRef = useRef(null)

  const slides = [
    {
      eyebrow: 'LG Home Week',
      title: '우리 집을 완성하는 베스트 추천 가전',
      description: '워시타워, 디오스 식기세척기, 코드제로 등 인기 제품을 한정 혜택가로 만나보세요.',
      bgImage: 'https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?auto=format&fit=crop&w=2000&q=80',
      primaryBtn: '혜택 보러가기',
      ghostBtn: '카테고리별 보기',
    },
    {
      eyebrow: '타임딜',
      title: 'LG 올레드 evo 특별전',
      description: '48형부터 86형까지 단계별 혜택, 수량 소진 시 조기 종료됩니다.',
      bgImage: 'https://images.unsplash.com/photo-1484100356142-db6ab6244067?auto=format&fit=crop&w=2000&q=80',
      primaryBtn: 'OLED 라인업 보기',
      ghostBtn: '장바구니 담기',
    },
    {
      eyebrow: "MD's Choice",
      title: '프리미엄 키친 스타일링',
      description: '시그니처 키친 스위트와 오브제컬렉션으로 완성하는 맞춤형 주방.',
      bgImage: 'https://images.unsplash.com/photo-1519710164239-da123dc03ef4?auto=format&fit=crop&w=2000&q=80',
      primaryBtn: '기획전 보기',
      ghostBtn: '상담 신청',
    },
  ]

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
  ]

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
  ]

  const handleStartOnboarding = () => {
    navigate('/onboarding')
  }

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length)
    resetTimer()
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length)
    resetTimer()
  }

  const goToSlide = (index) => {
    setCurrentSlide(index)
    resetTimer()
  }

  const startAutoplay = () => {
    timerRef.current = setInterval(nextSlide, 6000)
  }

  const resetTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
    startAutoplay()
  }

  useEffect(() => {
    startAutoplay()
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  const handleSliderMouseEnter = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
    }
  }

  const handleSliderMouseLeave = () => {
    startAutoplay()
  }

  return (
    <>
      <div className="utility-bar">
        <div className="container">
          <div className="utility-links">
            <a href="#">회사소개</a>
            <a href="#">사업자몰</a>
            <a href="#">마이페이지</a>
          </div>
          <button className="utility-btn">검색</button>
        </div>
      </div>

      <header className="global-header">
        <div className="container">
          <a className="logo" href="#">LG<span>전자</span></a>
          <nav className="gnb">
            <button className="gnb__item">TV/오디오</button>
            <button className="gnb__item">주방가전</button>
            <button className="gnb__item">생활가전</button>
            <button className="gnb__item">에어컨/에어케어</button>
            <button className="gnb__item">AI Home</button>
            <button className="gnb__item">LG Objet</button>
            <button className="gnb__item">LG SIGNATURE</button>
          </nav>
          <div className="actions">
            <button className="ghost">장바구니</button>
            <button className="primary" onClick={handleStartOnboarding}>로그인</button>
          </div>
        </div>
      </header>

      <main>
        <section className="hero" aria-label="LG 메인 프로모션">
          <div className="container">
            <div
              className="slider"
              ref={sliderRef}
              onMouseEnter={handleSliderMouseEnter}
              onMouseLeave={handleSliderMouseLeave}
            >
              <button
                className="slider__control prev"
                aria-label="이전"
                onClick={prevSlide}
              >
                &#10094;
              </button>
              <button
                className="slider__control next"
                aria-label="다음"
                onClick={nextSlide}
              >
                &#10095;
              </button>
              <div className="dots" aria-label="슬라이드 이동">
                {slides.map((_, index) => (
                  <button
                    key={index}
                    type="button"
                    aria-label={`${index + 1}번 슬라이드로 이동`}
                    className={currentSlide === index ? 'active' : ''}
                    onClick={() => goToSlide(index)}
                  />
                ))}
              </div>
              {slides.map((slide, index) => (
                <div
                  key={index}
                  className={`slide ${currentSlide === index ? 'active' : ''}`}
                  style={{ '--bg': `url('${slide.bgImage}')` }}
                >
                  <div className="slide__content">
                    <p className="eyebrow">{slide.eyebrow}</p>
                    <h1>{slide.title}</h1>
                    <p>{slide.description}</p>
                    <div className="cta-group">
                      <button className="primary" onClick={handleStartOnboarding}>
                        {slide.primaryBtn}
                      </button>
                      <button className="ghost">{slide.ghostBtn}</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="section" id="time-deal">
          <div className="container">
            <div className="section__head">
              <div>
                <p className="eyebrow">타임딜 · D-3</p>
                <h2>지금 담아야 할 LG 인기 제품</h2>
              </div>
              <a className="link" href="#">전체보기</a>
            </div>
            <div className="time-deal-grid">
              {timeDeals.map((deal, index) => (
                <article key={index} className="deal-card">
                  <span className="badge">{deal.badge}</span>
                  <h3>{deal.title}</h3>
                  <p>{deal.desc}</p>
                  <strong>{deal.price}</strong>
                  <small className="muted">{deal.stock}</small>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section section--highlight" id="home-week">
          <div className="container">
            <div className="section__head">
              <div>
                <p className="eyebrow">LG Home Week</p>
                <h2>우리 집을 완성하는 베스트 추천 가전</h2>
              </div>
              <a className="link" href="#">혜택 더 보기</a>
            </div>
            <div className="feature-row">
              <article className="feature-card">
                <h3>워시타워 오브제컬렉션</h3>
                <p>WL21WDU · 25/21kg · 에너지 1등급</p>
                <strong>최대혜택가 2,669,100원</strong>
              </article>
              <article className="feature-card">
                <h3>디오스 식기세척기</h3>
                <p>DUE4BGE · 스팀 · 1등급</p>
                <strong>최대혜택가 780,300원</strong>
              </article>
              <article className="feature-card">
                <h3>코드제로 A9S</h3>
                <p>AX920BWE · 흡입 전용</p>
                <strong>최대혜택가 688,200원</strong>
              </article>
            </div>
          </div>
        </section>

        <section className="section" id="md-choice">
          <div className="container">
            <div className="section__head">
              <div>
                <p className="eyebrow">MD's Choice</p>
                <h2>놓치기 아쉬운 특별한 가격</h2>
              </div>
              <a className="link" href="#">더보기</a>
            </div>
            <div className="product-grid">
              {mdChoice.map((item, index) => (
                <article key={index} className="product-card">
                  <span className="badge">{item.badge}</span>
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                  <strong>{item.price}</strong>
                  <button className="ghost" type="button">자세히 보기</button>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section categories">
          <div className="container">
            <div className="section__head">
              <div>
                <p className="eyebrow">바로가기</p>
                <h2>라이프스타일별 추천</h2>
              </div>
            </div>
            <div className="category-grid">
              <article>
                <h3>#홈엔터테인먼트</h3>
                <p>OLED · QNED · 사운드바</p>
              </article>
              <article>
                <h3>#결혼</h3>
                <p>신혼 패키지 · 혼수 혜택</p>
              </article>
              <article>
                <h3>#홈쿡</h3>
                <p>디오스 오븐 · 인덕션 · 큐커</p>
              </article>
              <article>
                <h3>#캠핑영화관</h3>
                <p>스탠바이미 · 시네빔 · 무드메이트</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <div className="container footer__grid">
          <div>
            <h4>LG전자 고객센터</h4>
            <p>궁금하신 점은 1588-7777 또는 챗봇으로 빠르게 해결하세요.</p>
          </div>
          <div>
            <h4>자주 찾는 링크</h4>
            <ul>
              <li><a href="#">배송 안내</a></li>
              <li><a href="#">교환/환불 정책</a></li>
              <li><a href="#">매장 상담 예약</a></li>
            </ul>
          </div>
          <div>
            <h4>팔로우</h4>
            <ul>
              <li><a href="#">Instagram</a></li>
              <li><a href="#">YouTube</a></li>
              <li><a href="#">Facebook</a></li>
            </ul>
          </div>
        </div>
        <div className="container footer__bottom">
          © 2025 LG Electronics. All Rights Reserved.
        </div>
      </footer>
    </>
  )
}

export default Section1
