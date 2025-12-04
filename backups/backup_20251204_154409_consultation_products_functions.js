/**
 * 구매상담예약 모달 제품정보 관련 함수 백업
 * 백업 일시: 2025-12-04 15:44:09
 * 
 * 이 파일은 result.html의 구매상담예약 모달에서 사용하는
 * 제품정보 로드 관련 함수들을 백업한 것입니다.
 */

// ============================================
// 전역 변수 (result.html에서 사용 중)
// ============================================
let globalRecommendations = [];

// ============================================
// 제품 정보 로드 함수
// ============================================
async function loadConsultationProducts() {
    const productsContainer = document.getElementById('consultationProducts');
    if (!productsContainer) {
        console.error('제품 컨테이너를 찾을 수 없습니다.');
        return;
    }

    productsContainer.innerHTML = '';

    // 먼저 전역 변수에서 추천 제품 정보 사용 시도
    let recommendations = globalRecommendations;
    console.log('전역 추천 제품 정보 사용:', recommendations);

    // 전역 변수에 데이터가 없으면 API 호출 시도
    if (!recommendations || recommendations.length === 0) {
        console.log('전역 변수에 데이터가 없어 API 호출 시도');
        try {
            const sessionId = sessionStorage.getItem('onboarding_session_id');
            if (!sessionId) {
                console.warn('세션 ID가 없습니다.');
                productsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">세션 정보를 찾을 수 없습니다.</div>';
                return;
            }

            const response = await fetch(`/api/onboarding/session/${sessionId}/`);
            if (!response.ok) {
                console.error('API 응답 오류:', response.status, response.statusText);
                // API 실패 시에도 페이지에 표시된 제품 정보 사용 시도
                recommendations = getProductsFromPage();
                if (!recommendations || recommendations.length === 0) {
                    productsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">제품 정보를 불러올 수 없습니다.</div>';
                    return;
                }
            } else {
                const data = await response.json();
                if (data.success && data.session && data.session.recommendation_result) {
                    let recommendationResult = data.session.recommendation_result;
                    if (typeof recommendationResult === 'string') {
                        try {
                            recommendationResult = JSON.parse(recommendationResult);
                        } catch (e) {
                            console.error('추천 결과 파싱 오류:', e);
                        }
                    }
                    recommendations = recommendationResult.recommendations || [];
                    globalRecommendations = recommendations; // 전역 변수에 저장

                    // API에서 가져온 recommendations가 비어있으면 페이지에서 가져오기 시도
                    if (!recommendations || recommendations.length === 0) {
                        console.log('API 응답에 제품이 없어 페이지에서 제품 정보를 가져오는 중...');
                        recommendations = getProductsFromPage();
                    }
                } else {
                    // API 응답에 recommendation_result가 없으면 페이지에서 가져오기 시도
                    console.log('API 응답에 recommendation_result가 없어 페이지에서 제품 정보를 가져오는 중...');
                    recommendations = getProductsFromPage();
                }
            }
        } catch (error) {
            console.error('API 호출 오류:', error);
            // API 실패 시에도 페이지에 표시된 제품 정보 사용 시도
            recommendations = getProductsFromPage();
            if (!recommendations || recommendations.length === 0) {
                productsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">제품 정보를 불러오는 중 오류가 발생했습니다.</div>';
                return;
            }
        }
    }

    console.log('최종 추천 제품 목록:', recommendations);

    // 여전히 제품이 없으면 페이지에서 직접 가져오기 시도
    if (!recommendations || recommendations.length === 0) {
        console.log('추천 제품이 없어 페이지에서 제품 정보를 가져오는 중...');
        recommendations = getProductsFromPage();
        console.log('페이지에서 가져온 제품 정보:', recommendations);
    }

    if (!recommendations || recommendations.length === 0) {
        console.warn('추천 제품이 없습니다.');
        productsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">추천 제품이 없습니다.</div>';
        return;
    }

    // 제품 이미지 로드를 위한 비동기 함수
    const loadProductImageForConsultation = async (productName, imgElement) => {
        try {
            const response = await fetch(`/api/products/image-by-name/?name=${encodeURIComponent(productName)}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.image_url) {
                    imgElement.src = data.image_url;
                }
            }
        } catch (error) {
            console.error('제품 이미지 로드 오류:', error);
        }
    };

    // 제품 타입에 따른 가전 카테고리 이미지 매핑
    const getApplianceCategoryImage = (productName, index) => {
        const categoryImages = {
            '냉장고': '/static/images/가전 카테고리/냉장고.png',
            '광파오븐': '/static/images/가전 카테고리/광파오븐.png',
            '식기세척기': '/static/images/가전 카테고리/식기세척기.png'
        };

        // 제품명에서 카테고리 추출
        if (productName.includes('냉장고')) {
            return categoryImages['냉장고'];
        } else if (productName.includes('광파오븐') || productName.includes('오븐')) {
            return categoryImages['광파오븐'];
        } else if (productName.includes('식기세척기')) {
            return categoryImages['식기세척기'];
        }

        // 인덱스 기반 매핑 (첫 번째: 냉장고, 두 번째: 광파오븐, 세 번째: 식기세척기)
        const indexMapping = [
            categoryImages['냉장고'],
            categoryImages['광파오븐'],
            categoryImages['식기세척기']
        ];

        return indexMapping[index] || categoryImages['냉장고'];
    };

    // 모델명 매핑 (순서대로: 냉장고, 광파오븐, 식기세척기)
    const modelNumberMapping = ['W826GBB482', 'MLJ32ERS', 'DUE5BGHE'];

    recommendations.forEach((product, index) => {
        console.log(`제품 ${index + 1} 처리 중:`, product);
        const productItem = document.createElement('div');
        productItem.className = 'consultation-product-item';

        // 가전 카테고리 이미지 사용
        const imageUrl = getApplianceCategoryImage(product.name || '', index);
        const productName = product.name || '제품명 없음';
        // 모델명: 제품 데이터에 있으면 사용, 없으면 매핑된 모델명 사용
        const modelNumber = product.model_number || product.model || (modelNumberMapping[index] || '');

        // 가격 정보: 정가, 판매가, 최대 혜택가
        const originalPrice = product.original_price || product.price || 0;
        const salePrice = product.sale_price || product.price || 0;
        const discountPrice = product.discount_price || salePrice || product.price || 0;

        // 할인율 계산: 정가 기준으로 최대 혜택가와 비교
        const discountRate = originalPrice > 0 && discountPrice < originalPrice
            ? Math.round((1 - discountPrice / originalPrice) * 100)
            : 0;

        // 가격 포맷팅 (원 단위 제거, 숫자만)
        const formatPriceNumber = (price) => {
            if (!price || price === 0) return '0';
            return formatPrice(price);
        };

        // 제품 설명 가져오기
        const productDescription = product.reason || product.description || '';

        productItem.innerHTML = `
            <button class="consultation-product-remove" onclick="removeProduct(this)">×</button>
            <img src="${imageUrl}" alt="${productName}" class="consultation-product-image" onerror="this.src='/static/images/가전 카테고리/냉장고.png'">
            <div class="consultation-product-info">
                <div class="consultation-product-name">${productName}</div>
                <div class="consultation-product-model">${modelNumber}</div>
                ${productDescription ? `<div class="consultation-product-description">${productDescription}</div>` : ''}
                <div class="consultation-product-price-info">
                    ${discountRate > 0 ? `<span class="consultation-product-discount-rate">${discountRate}%</span>` : ''}
                    <span class="consultation-product-benefit-price">${formatPriceNumber(discountPrice)}</span>
                    <span class="consultation-product-original-price">${formatPriceNumber(originalPrice)}</span>
                </div>
            </div>
        `;

        productsContainer.appendChild(productItem);
        console.log(`제품 ${index + 1} 추가 완료:`, productName);
    });

    console.log(`총 ${recommendations.length}개 제품이 추가되었습니다.`);
}

// ============================================
// 페이지에서 직접 제품 정보 가져오기 함수
// (API 실패 시 대체 방법)
// ============================================
function getProductsFromPage() {
    const products = [];
    const productIds = ['refrigerator', 'microwave', 'dishwasher'];

    console.log('페이지에서 제품 정보 추출 시작...');

    productIds.forEach((productId, index) => {
        const productElement = document.getElementById(`product-${productId}`);
        console.log(`제품 ${productId} 요소 찾기:`, productElement ? '찾음' : '없음');

        if (productElement) {
            const titleElement = productElement.querySelector('.product-title');
            const imageElement = document.getElementById(`product-image-${productId}`);

            if (titleElement) {
                const productName = titleElement.textContent.trim();
                const imageUrl = imageElement ? imageElement.src : '';

                console.log(`제품 ${productId} 정보:`, {
                    name: productName,
                    imageUrl: imageUrl
                });

                // 가격 정보 가져오기
                const priceOriginalEl = productElement.querySelector('.price-original');
                const priceSaleEl = productElement.querySelector('.price-sale');
                const priceFinalEl = productElement.querySelector('.price-final');

                let originalPrice = 0;
                let salePrice = 0;
                let discountPrice = 0;

                if (priceOriginalEl) {
                    originalPrice = parseInt(priceOriginalEl.textContent.replace(/[^0-9]/g, '')) || 0;
                }
                if (priceSaleEl) {
                    salePrice = parseInt(priceSaleEl.textContent.replace(/[^0-9]/g, '')) || 0;
                }
                if (priceFinalEl) {
                    discountPrice = parseInt(priceFinalEl.textContent.replace(/[^0-9]/g, '')) || 0;
                }

                // 제품 설명 가져오기 (추천 이유)
                const reasonTextEl = productElement.querySelector('.recommend-reason-text');
                const productDescription = reasonTextEl ? reasonTextEl.textContent.trim() : '';

                products.push({
                    name: productName,
                    image_url: imageUrl,
                    original_price: originalPrice,
                    sale_price: salePrice,
                    discount_price: discountPrice || salePrice || originalPrice,
                    price: originalPrice || salePrice || discountPrice,
                    reason: productDescription,
                    description: productDescription
                });

                console.log(`제품 ${productId} 추가 완료:`, productName);
            } else {
                console.warn(`제품 ${productId}의 제목 요소를 찾을 수 없습니다.`);
            }
        } else {
            console.warn(`제품 요소 #product-${productId}를 찾을 수 없습니다.`);
        }
    });

    console.log(`페이지에서 총 ${products.length}개 제품 추출 완료:`, products);
    return products;
}

// ============================================
// 사용 방법
// ============================================
/*
이 함수들은 result.html에서 다음과 같이 사용됩니다:

1. 구매상담예약 모달이 열릴 때:
   - openConsultationModal() 함수에서 loadConsultationProducts() 호출

2. 제품 정보 로드 순서:
   - 먼저 전역 변수 globalRecommendations에서 가져오기 시도
   - 없으면 세션 ID로 API 호출 (/api/onboarding/session/{sessionId}/)
   - API 실패 시 페이지에서 직접 제품 정보 추출 (getProductsFromPage())

3. 제품 정보 표시:
   - 제품명, 모델명, 가격 정보, 할인율, 제품 설명 등을 표시
   - 가전 카테고리 이미지 사용 (냉장고, 광파오븐, 식기세척기)
   - 모델명 매핑: W826GBB482, MLJ32ERS, DUE5BGHE

4. 오류 처리:
   - 세션 ID가 없으면 "세션 정보를 찾을 수 없습니다." 메시지 표시
   - API 실패 시 페이지에서 제품 정보 추출 시도
   - 모든 방법이 실패하면 "제품 정보를 불러올 수 없습니다." 메시지 표시
*/

