// Smooth scroll for anchor links
document.addEventListener('DOMContentLoaded', () => {
    // GNB smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const headerOffset = 64;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form submit handler
    const form = document.getElementById('recommend-form');
    if (form) {
        form.addEventListener('submit', submitRecommendForm);
    }
});

async function submitRecommendForm(event) {
    event.preventDefault();

    const form = document.getElementById('recommend-form');
    if (!form) return;

    const payload = {
        vibe: form.querySelector('select[name="vibe"]').value,
        household_size: Number(form.querySelector('input[name="household_size"]').value),
        housing_type: form.querySelector('select[name="housing_type"]').value,
        main_space: "living",
        space_size: "medium",
        cook_freq: null,
        laundry_pattern: null,
        media_usage: null,
        priority: form.querySelector('select[name="priority"]').value,
        budget_level: form.querySelector('select[name="budget_level"]').value,
        target_categories: ["TV"]
    };

    const loading = document.getElementById('loading');
    const resultDiv = document.getElementById('recommend-result');

    // Show loading
    if (loading) {
        loading.style.display = 'block';
    }
    if (resultDiv) {
        resultDiv.innerHTML = '';
    }

    try {
        const res = await fetch('/api/recommend/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();

        // 새로운 API 응답 형식 지원 (success, count, recommendations)
        const recommendations = data.recommendations || [];
        
        if (!data.success || !recommendations || recommendations.length === 0) {
            if (resultDiv) {
                const errorMsg = data.error || data.message || '추천 결과가 없습니다.';
                resultDiv.innerHTML = `<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">${errorMsg}</p>`;
            }
            return;
        }

        // Render recommendations
        if (resultDiv) {
            recommendations.forEach(item => {
                const card = document.createElement('div');
                card.className = 'product-card';
                
                const price = item.discount_price || item.price || 0;
                const originalPrice = item.discount_price && item.price ? item.price : null;
                
                card.innerHTML = `
                    <h3>${escapeHtml(item.name || item.model || '')}</h3>
                    ${item.model_number ? `<p class="model">${escapeHtml(item.model_number)}</p>` : ''}
                    <p class="price">
                        ${price.toLocaleString()}원
                        ${originalPrice ? `<span style="font-size: 0.8em; color: var(--text-secondary); text-decoration: line-through; margin-left: 0.5rem;">${originalPrice.toLocaleString()}원</span>` : ''}
                    </p>
                    ${item.reason ? `<p class="reason">${escapeHtml(item.reason)}</p>` : ''}
                    ${item.score ? `<p class="score" style="font-size: 0.85em; color: var(--lg-primary); margin-top: 0.5rem;">추천 점수: ${(item.score * 100).toFixed(0)}%</p>` : ''}
                `;
                
                resultDiv.appendChild(card);
            });
        }

    } catch (err) {
        console.error('Error fetching recommendations:', err);
        if (resultDiv) {
            resultDiv.innerHTML = '<p style="text-align: center; color: #d32f2f; padding: 2rem;">추천 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.</p>';
        }
    } finally {
        // Hide loading
        if (loading) {
            loading.style.display = 'none';
        }
    }
}

// XSS 방지를 위한 HTML 이스케이프 함수
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
