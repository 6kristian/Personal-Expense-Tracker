document.addEventListener('DOMContentLoaded', () => {
    // Fetch pricing data from the server
    fetch('/pricing')
        .then(response => response.json())
        .then(data => {
            const pricingContainer = document.getElementById('pricing-plans');
            pricingContainer.innerHTML = ''; // Clear any existing content

            // Dynamically create pricing cards
            data.forEach(plan => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <h2>${plan.name}</h2>
                    <p class="price">$${plan.price} <span>/month</span></p>
                    <ul>
                        ${plan.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                    <button>Select Plan</button>
                `;
                pricingContainer.appendChild(card);
            });
        })
        .catch(error => console.error('Error fetching pricing data:', error));
});

// Function to show the processing message
function showProcessing(plan) {
    const processingDiv = document.getElementById('processing-message');
    const planName = document.getElementById('plan-name');
    planName.textContent = `Thank you for selecting the ${plan} plan!`;
    processingDiv.classList.remove('processing-hidden');
    processingDiv.classList.add('processing-visible');
}

// Function to hide the processing message
function hideProcessing() {
    const processingDiv = document.getElementById('processing-message');
    processingDiv.classList.remove('processing-visible');
    processingDiv.classList.add('processing-hidden');
}
