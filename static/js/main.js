// Mobile Menu Toggle
const mobileBtn = document.getElementById('mobileMenuBtn');
const navMenu = document.getElementById('navMenu');

if (mobileBtn) {
    mobileBtn.addEventListener('click', () => {
        navMenu.classList.toggle('active');
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });
}

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    if (navMenu && navMenu.classList.contains('active')) {
        if (!navMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
});

// Search functionality
const searchBtn = document.getElementById('searchBtn');
const searchDropdown = document.getElementById('searchDropdown');
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        searchDropdown.classList.toggle('active');
        if (searchDropdown.classList.contains('active')) {
            searchInput.focus();
        }
    });
}

// Close search on outside click
document.addEventListener('click', (e) => {
    if (searchDropdown && searchDropdown.classList.contains('active')) {
        if (!searchDropdown.contains(e.target) && !searchBtn.contains(e.target)) {
            searchDropdown.classList.remove('active');
        }
    }
});

// Live search
if (searchInput) {
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            searchResults.innerHTML = data.results.map(result => `
                                <a href="${result.url}" class="search-result-item">
                                    <strong>${result.name}</strong>
                                    <small style="display: block; color: #888;">${result.category}</small>
                                </a>
                            `).join('');
                        } else {
                            searchResults.innerHTML = '<div class="search-result-item">No products found</div>';
                        }
                    })
                    .catch(error => {
                        console.error('Search error:', error);
                    });
            } else {
                searchResults.innerHTML = '';
            }
        }, 300);
    });
}

// Newsletter Subscription
const newsletterForm = document.getElementById('newsletterForm');
const newsletterMessage = document.getElementById('newsletterMessage');

if (newsletterForm) {
    newsletterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('newsletterEmail').value;
        
        try {
            const response = await fetch('/newsletter/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `email=${encodeURIComponent(email)}`
            });
            
            const data = await response.json();
            newsletterMessage.textContent = data.message || data.error;
            newsletterMessage.style.color = response.ok ? '#10B981' : '#EF4444';
            
            if (response.ok) {
                newsletterForm.reset();
                setTimeout(() => {
                    newsletterMessage.textContent = '';
                }, 3000);
            }
        } catch (error) {
            newsletterMessage.textContent = 'Subscription failed. Please try again.';
            newsletterMessage.style.color = '#EF4444';
        }
    });
}

// Smooth Scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.service-card, .product-card, .feature').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'all 0.6s ease';
    observer.observe(el);
});

// Lazy loading images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.getAttribute('data-src');
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                }
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}