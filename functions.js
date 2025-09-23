// NormScout Landing Page Interactive Functions

document.addEventListener('DOMContentLoaded', function() {
    initializeMobileMenu();
    initializeSmoothScrolling();
    initializeDemoSection();
    initializeAnimations();
    initializeEnhancedFormInteractions();
});

// Mobile Menu Functionality
function initializeMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const nav = document.getElementById('nav');
    
    if (mobileMenuToggle && nav) {
        mobileMenuToggle.addEventListener('click', function() {
            nav.classList.toggle('mobile-nav-open');
            mobileMenuToggle.classList.toggle('mobile-menu-active');
            
            // Animate hamburger menu
            const spans = mobileMenuToggle.querySelectorAll('span');
            if (mobileMenuToggle.classList.contains('mobile-menu-active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
        
        // Close mobile menu when clicking nav links
        const navLinks = nav.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                nav.classList.remove('mobile-nav-open');
                mobileMenuToggle.classList.remove('mobile-menu-active');
                
                const spans = mobileMenuToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });
    }
}

// Smooth Scrolling for Navigation Links
function initializeSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                // Calculate offset for fixed header
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;
                
                // Smooth scroll to target
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Add visual feedback for demo cards when coming from step cards
                if (targetId === '#demo' && this.classList.contains('step-card-link')) {
                    setTimeout(() => {
                        highlightDemoCards();
                    }, 500);
                }
            }
        });
    });
}

// Demo Section Functionality
function initializeDemoSection() {
    // Show demo section when "Try Now" is clicked
    const tryNowButtons = document.querySelectorAll('a[href="#demo"]');
    tryNowButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            showDemoSection();
        });
    });
}

function showDemoSection() {
    const demoSection = document.getElementById('demo');
    if (demoSection) {
        demoSection.style.display = 'block';
        // Smooth reveal animation
        setTimeout(() => {
            demoSection.style.opacity = '0';
            demoSection.style.transform = 'translateY(20px)';
            demoSection.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                demoSection.style.opacity = '1';
                demoSection.style.transform = 'translateY(0)';
            }, 50);
        }, 100);
    }
}

// Demo Form Functionality
// Helper function to format markdown-like text to HTML
function formatMarkdownToHTML(text) {
    if (!text) return '';

    // Convert markdown to HTML
    return text
        .replace(/### (.*?)(?:\n|$)/g, '<h3 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.2em;">$1</h3>')
        .replace(/## (.*?)(?:\n|$)/g, '<h2 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.4em;">$1</h2>')
        .replace(/# (.*?)(?:\n|$)/g, '<h1 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.6em;">$1</h1>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/#### (.*?)(?:\n|$)/g, '<h4 style="color: #333; margin: 15px 0 8px 0; font-size: 1.1em;">$1</h4>')
        .replace(/^- (.*?)$/gm, '<li style="margin: 5px 0;">$1</li>')
        .replace(/(<li[^>]*>.*<\/li>\s*)+/g, '<ul style="margin: 10px 0; padding-left: 25px;">$&</ul>')
        .replace(/\n\n/g, '</p><p style="margin: 12px 0; line-height: 1.6;">')
        .replace(/\n/g, '<br>');
}

function startDemo() {
    const productDescription = document.getElementById('product-description').value;
    const countrySelector = document.getElementById('country-selector').value;

    if (!productDescription.trim()) {
        alert('Please describe your product first.');
        return;
    }

    if (!countrySelector) {
        alert('Please select a country.');
        return;
    }

    const button = event.currentTarget || event.target;
    const originalHTML = button.innerHTML;

    // Add loading animation with inline spinner
    button.innerHTML = '<span class="spinner"></span> Analyzing regulations...';
    button.disabled = true;
    button.style.opacity = '0.8';

    fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            product: productDescription,
            country: countrySelector
        })
    })
    .then(response => response.json())
    .then(data => {
        showDemoResults(productDescription, countrySelector, data.result);
        button.innerHTML = originalHTML;
        button.disabled = false;
        button.style.opacity = '1';
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("Backend connection failed; try again later");
        button.innerHTML = originalHTML;
        button.disabled = false;
        button.style.opacity = '1';
    });
}

function showDemoResults(product, country, backendResult) {
    const countryNames = {
        'us': 'United States',
        'eu': 'European Union',
        'uk': 'United Kingdom',
        'ca': 'Canada',
        'au': 'Australia',
        'jp': 'Japan',
        'ch': 'Switzerland'
    };
    
    const mockResults = `
        <div style="
            background: #f8f9fa; 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            padding: 24px; 
            margin-top: 24px; 
            text-align: left;
        ">
            <h3 style="color: #2048D5; margin-bottom: 16px;"> Demo Results</h3>
            <p><strong>Product:</strong> ${product}</p>
            <p><strong>Target Market:</strong> ${countryNames[country] || country}</p>
            <div style="margin-top: 20px; padding: 20px; background: #f0f7ff; border-radius: 8px;">
                <h4 style="color: #2048D5; margin-bottom: 12px;">Analysis Results:</h4>
                <div style="line-height: 1.8; color: #333;">
                    ${formatMarkdownToHTML(backendResult)}
                </div>
            </div>
            <div style="margin-top: 16px;">
                <button onclick="contactForFullAccess()" style="
                    background: #448CF7; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 6px; 
                    cursor: pointer;
                ">Get Full Access</button>
            </div>
        </div>
    `;
    
    const demoSection = document.querySelector('.demo-section');
    if (demoSection) {
        demoSection.innerHTML += mockResults;
    }
}

function contactForFullAccess() {
    alert('Thank you for your interest! Please contact us at hello@normscout.ch for full access and investor information.');
}

// Highlight demo cards with animation
function highlightDemoCards() {
    const demoCards = document.querySelectorAll('.demo-card');
    demoCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.transform = 'scale(1.02)';
            card.style.borderColor = '#448CF7';
            card.style.boxShadow = '0 10px 25px rgba(68, 140, 247, 0.15)';
            
            setTimeout(() => {
                card.style.transform = '';
                card.style.borderColor = '';
                card.style.boxShadow = '';
            }, 800);
        }, index * 100);
    });
}

// Enhanced form interactions
function initializeEnhancedFormInteractions() {
    const productInput = document.getElementById('product-description');
    const countrySelect = document.getElementById('country-selector');
    
    if (productInput) {
        // Auto-resize textarea
        productInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Focus card highlighting
        productInput.addEventListener('focus', function() {
            const card = this.closest('.demo-card');
            if (card) {
                card.style.borderColor = '#448CF7';
                card.style.boxShadow = '0 8px 20px rgba(68, 140, 247, 0.12)';
            }
        });
        
        productInput.addEventListener('blur', function() {
            const card = this.closest('.demo-card');
            if (card) {
                card.style.borderColor = '';
                card.style.boxShadow = '';
            }
        });
    }
    
    if (countrySelect) {
        countrySelect.addEventListener('focus', function() {
            const card = this.closest('.demo-card');
            if (card) {
                card.style.borderColor = '#448CF7';
                card.style.boxShadow = '0 8px 20px rgba(68, 140, 247, 0.12)';
            }
        });
        
        countrySelect.addEventListener('blur', function() {
            const card = this.closest('.demo-card');
            if (card) {
                card.style.borderColor = '';
                card.style.boxShadow = '';
            }
        });
        
        countrySelect.addEventListener('change', function() {
            if (this.value) {
                const card = this.closest('.demo-card');
                if (card) {
                    card.style.borderColor = '#2048D5';
                    setTimeout(() => {
                        card.style.borderColor = '';
                    }, 1000);
                }
            }
        });
    }
}

// Scroll Animations
function initializeAnimations() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.step-card, .metric-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 100) {
        header.style.backgroundColor = 'rgba(255, 255, 255, 0.98)';
        header.style.backdropFilter = 'blur(15px)';
    } else {
        header.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        header.style.backdropFilter = 'blur(10px)';
    }
});

// Form enhancements
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('product-description');
    const selector = document.getElementById('country-selector');
    
    if (textarea) {
        textarea.addEventListener('input', function() {
            // Auto-resize textarea
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Placeholder animation
        textarea.addEventListener('focus', function() {
            this.style.borderColor = '#448CF7';
        });
        
        textarea.addEventListener('blur', function() {
            this.style.borderColor = '#EEF0F3';
        });
    }
    
    if (selector) {
        selector.addEventListener('change', function() {
            this.style.borderColor = this.value ? '#448CF7' : '#EEF0F3';
        });
    }
});

// Analytics simulation (for investor demo)
function trackDemoUsage() {
    console.log('Demo usage tracked:', {
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        referrer: document.referrer
    });
}

// Add mobile menu styles dynamically
const style = document.createElement('style');
style.textContent = `
    @media (max-width: 767px) {
        .nav {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 16px;
            display: none;
            flex-direction: column;
            gap: 16px;
        }
        
        .nav.mobile-nav-open {
            display: flex;
        }
        
        .mobile-menu-toggle span {
            transition: all 0.3s ease;
        }
    }
`;
document.head.appendChild(style);