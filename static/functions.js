// NormScout Landing Page Interactive Functions

document.addEventListener('DOMContentLoaded', function() {
    initializeMobileMenu();
    initializeSmoothScrolling();
    initializeDemoSection();
    initializeAnimations();
    initializeEnhancedFormInteractions();
    initializeVisitorCounter();
});

// Visitor Counter Functionality
function initializeVisitorCounter() {
    // First, increment the visitor count
    fetch('/api/visitor-count', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const counterElement = document.getElementById('monthly-users-count');
        if (counterElement && data.count) {
            counterElement.textContent = data.count.toLocaleString();
        }
    })
    .catch(error => {
        console.log('Visitor counter unavailable:', error);
        const counterElement = document.getElementById('monthly-users-count');
        if (counterElement) counterElement.textContent = '---';
    });

    // Then fetch all metrics
    fetch('/api/metrics')
    .then(response => response.json())
    .then(data => {
        // Update products searched
        const productsElement = document.getElementById('products-searched-count');
        if (productsElement && data.products_searched !== undefined) {
            productsElement.textContent = data.products_searched.toLocaleString();
        }

        // Update norms scouted with + sign
        const normsElement = document.getElementById('norms-scouted-count');
        if (normsElement && data.norms_scouted !== undefined) {
            normsElement.textContent = data.norms_scouted.toLocaleString() + '+';
        }

        // Update monthly users if not already set
        const usersElement = document.getElementById('monthly-users-count');
        if (usersElement && usersElement.textContent === '...' && data.monthly_users !== undefined) {
            usersElement.textContent = data.monthly_users.toLocaleString();
        }

        // Update investment section stats (same data, different location)
        const investmentNormsElement = document.getElementById('investment-norms-count');
        if (investmentNormsElement && data.norms_scouted !== undefined) {
            investmentNormsElement.textContent = data.norms_scouted.toLocaleString() + '+';
        }

        const investmentProductsElement = document.getElementById('investment-products-count');
        if (investmentProductsElement && data.products_searched !== undefined) {
            investmentProductsElement.textContent = data.products_searched.toLocaleString();
        }

        const investmentUsersElement = document.getElementById('investment-users-count');
        if (investmentUsersElement && data.monthly_users !== undefined) {
            investmentUsersElement.textContent = data.monthly_users.toLocaleString();
        }
    })
    .catch(error => {
        console.log('Metrics unavailable:', error);
        document.getElementById('products-searched-count').textContent = '---';
        document.getElementById('norms-scouted-count').textContent = '---';
        document.getElementById('investment-norms-count').textContent = '---';
        document.getElementById('investment-products-count').textContent = '---';
        document.getElementById('investment-users-count').textContent = '---';
    });
}

// Counter animation function
function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    const difference = end - start;

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function for smoother animation
        const easeOutQuad = progress * (2 - progress);
        const currentValue = Math.floor(start + (difference * easeOutQuad));

        element.textContent = currentValue.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = end.toLocaleString();
        }
    }

    requestAnimationFrame(updateCounter);
}

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
                
                // Add visual feedback for demo cards when clicking any link to demo
                if (targetId === '#demo') {
                    setTimeout(() => {
                        highlightDemoCardsSequentially();
                    }, 600);
                }
            }
        });
    });
}

// Demo Section Functionality
function initializeDemoSection() {
    // No need for separate handler - smooth scrolling handles everything
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

    // Clean up problematic patterns
    // Remove lone # symbols that appear as section separators
    // More aggressive: any # on a line by itself (with optional whitespace)
    text = text.replace(/^\s*#\s*$/gm, '')
           // Also remove # that appear between sections (with newline before and after)
           .replace(/\n\s*#\s*\n/g, '\n\n');

    // Convert markdown to HTML - process lists first to avoid paragraph breaks
    text = text
        // Convert bullet points to list items with tight spacing
        .replace(/^- (.*?)$/gm, '<li>$1</li>')
        // Group consecutive list items into <ul> tags
        .replace(/(<li>.*<\/li>\s*)+/g, function(match) {
            // Remove any line breaks between list items for tighter spacing
            const cleaned = match.replace(/<\/li>\s*\n\s*<li>/g, '</li><li>');
            return '<ul style="margin: 10px 0; padding-left: 25px; line-height: 1.4;">' + cleaned + '</ul>';
        });

    // Now process other markdown elements
    text = text
        .replace(/### (.*?)(?:\n|$)/g, '<h3 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.2em;">$1</h3>')
        .replace(/## (.*?)(?:\n|$)/g, '<h2 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.4em;">$1</h2>')
        .replace(/# (.*?)(?:\n|$)/g, '<h1 style="color: #2048D5; margin: 20px 0 10px 0; font-size: 1.6em;">$1</h1>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/#### (.*?)(?:\n|$)/g, '<h4 style="color: #333; margin: 15px 0 8px 0; font-size: 1.1em;">$1</h4>')
        .replace(/\n\n/g, '</p><p style="margin: 12px 0; line-height: 1.6;">')
        .replace(/\n/g, '<br>');

    // Final cleanup: remove any standalone # or &#35; that appear after HTML tags
    text = text.replace(/>(\s*<br>)*\s*#\s*(<br>)*/g, '>$1$2')
               .replace(/&#35;/g, '');

    return text;
}

// Store original button HTML globally
let demoButtonOriginalHTML = null;

// Function to update metrics display
function updateMetricsDisplay() {
    // Fetch updated metrics
    fetch('/api/metrics')
    .then(response => response.json())
    .then(data => {
        // Update products searched with animation (just the increment)
        const productsElement = document.getElementById('products-searched-count');
        if (productsElement && data.products_searched !== undefined) {
            // Parse current value removing commas
            const currentText = productsElement.textContent.replace(/,/g, '');
            const currentValue = parseInt(currentText) || 0;

            // Only animate if value increased
            if (data.products_searched > currentValue) {
                animateCounter(productsElement, currentValue, data.products_searched, 800);
            }
        }

        // Update norms scouted with smoother animation
        const normsElement = document.getElementById('norms-scouted-count');
        if (normsElement && data.norms_scouted !== undefined) {
            // Remove the '+' and commas for parsing
            const currentText = normsElement.textContent.replace('+', '').replace(/,/g, '');
            const currentValue = parseInt(currentText) || 0;

            // Only animate if value increased, with slower animation for visual effect
            if (data.norms_scouted > currentValue) {
                // Calculate the increment for smoother animation
                const increment = data.norms_scouted - currentValue;
                // Slower animation for bigger numbers (2-3 seconds based on increment)
                const duration = Math.min(2000 + (increment * 50), 3000);
                animateCounterWithPlus(normsElement, currentValue, data.norms_scouted, duration);
            }
        }

        // Also update investment section stats with animations
        const investmentProductsElement = document.getElementById('investment-products-count');
        if (investmentProductsElement && data.products_searched !== undefined) {
            const currentText = investmentProductsElement.textContent.replace(/,/g, '');
            const currentValue = parseInt(currentText) || 0;

            if (data.products_searched > currentValue) {
                animateCounter(investmentProductsElement, currentValue, data.products_searched, 800);
            }
        }

        const investmentNormsElement = document.getElementById('investment-norms-count');
        if (investmentNormsElement && data.norms_scouted !== undefined) {
            const currentText = investmentNormsElement.textContent.replace('+', '').replace(/,/g, '');
            const currentValue = parseInt(currentText) || 0;

            if (data.norms_scouted > currentValue) {
                const increment = data.norms_scouted - currentValue;
                const duration = Math.min(2000 + (increment * 50), 3000);
                animateCounterWithPlus(investmentNormsElement, currentValue, data.norms_scouted, duration);
            }
        }

        const investmentUsersElement = document.getElementById('investment-users-count');
        if (investmentUsersElement && data.monthly_users !== undefined) {
            const currentText = investmentUsersElement.textContent.replace(/,/g, '');
            const currentValue = parseInt(currentText) || 0;

            if (data.monthly_users > currentValue) {
                animateCounter(investmentUsersElement, currentValue, data.monthly_users, 800);
            }
        }
    })
    .catch(error => {
        console.log('Could not update metrics:', error);
    });
}

// Special animation function for counters with '+' sign
function animateCounterWithPlus(element, start, end, duration) {
    const startTime = performance.now();
    const difference = end - start;

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function for smoother animation
        const easeOutQuad = progress * (2 - progress);
        const currentValue = Math.floor(start + (difference * easeOutQuad));

        element.textContent = currentValue.toLocaleString() + '+';

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = end.toLocaleString() + '+';
        }
    }

    requestAnimationFrame(updateCounter);
}

function clearPreviousResults() {
    // This function is now deprecated - we handle clearing at the right time
}

function clearDemoResults() {
    // Clear demo results container
    const resultsContainer = document.getElementById('demo-results-container');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

// Function to highlight field with blue glow animation
function highlightField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        // Remove the class first to reset animation if it's already present
        field.classList.remove('validation-error');
        // Force a reflow to restart the animation
        void field.offsetWidth;
        // Add the class to trigger animation
        field.classList.add('validation-error');

        // Focus the field for better user experience
        field.focus();

        // Remove the class after animation completes (1.2 seconds for 2 pulses)
        setTimeout(() => {
            field.classList.remove('validation-error');
        }, 1200);
    }
}

function startDemo(event) {
    const productDescription = document.getElementById('product-description').value;
    const countrySelector = document.getElementById('country-selector').value;

    if (!productDescription.trim()) {
        highlightField('product-description');
        return;
    }

    if (!countrySelector) {
        highlightField('country-selector');
        return;
    }

    // Don't clear anything here - wait for response

    // Get button from event or find it by class
    const button = event ? (event.currentTarget || event.target) : document.querySelector('.demo-button');

    // Store original HTML only once (first time)
    if (!demoButtonOriginalHTML) {
        demoButtonOriginalHTML = button.innerHTML;
    }

    // Add loading animation with inline spinner
    button.innerHTML = '<span class="spinner"></span> Analyzing regulations...';
    button.disabled = true;
    button.style.opacity = '0.8';
    button.classList.add('loading');

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
        // Always reset button first, regardless of result
        button.innerHTML = demoButtonOriginalHTML;
        button.disabled = false;
        button.style.opacity = '1';
        button.classList.remove('loading');

        // Then handle the response
        if (data.status === 'invalid' && data.show_fields) {
            // Invalid product - load error fields (loadFieldBlocks handles clearing)
            clearDemoResults(); // Clear any old demo results
            loadFieldBlocks();
        } else {
            // Valid product - show new results (automatically replaces old ones)
            clearFieldBlocks(); // Clear any error fields
            showDemoResults(productDescription, countrySelector, data.result);

            // Update the metrics to show increased counts
            updateMetricsDisplay();
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert("Backend connection failed; try again later");

        // Reset button on error
        button.innerHTML = demoButtonOriginalHTML;
        button.disabled = false;
        button.style.opacity = '1';
        button.classList.remove('loading');
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
    
    // Find or create a container for results
    let resultsContainer = document.getElementById('demo-results-container');
    if (!resultsContainer) {
        const demoSection = document.querySelector('.demo-section');
        if (demoSection) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'demo-results-container';
            demoSection.appendChild(resultsContainer);
        }
    }

    if (resultsContainer) {
        // Replace content instead of appending
        resultsContainer.innerHTML = mockResults;
    }
}

function contactForFullAccess() {
    alert('Thank you for your interest! Please contact us at hello@normscout.ch for full access and investor information.');
}

// Highlight demo cards with blue glow animation sequentially
function highlightDemoCardsSequentially() {
    const demoCards = document.querySelectorAll('.demo-card');
    demoCards.forEach((card, index) => {
        setTimeout(() => {
            // Apply the demo-card-highlight class (single pulse)
            card.classList.add('demo-card-highlight');

            // Remove the class after animation completes
            setTimeout(() => {
                card.classList.remove('demo-card-highlight');
            }, 900);
        }, index * 100); // Faster stagger - only 100ms between cards
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

// ========== FIELD FRAMEWORK FUNCTIONS ==========
// Functions to dynamically load and render field blocks

function clearFieldBlocks() {
    const container = document.getElementById('dynamic-fields-container');
    if (container) {
        container.innerHTML = '';
    }
}

async function loadFieldBlocks() {
    try {
        const response = await fetch('/api/fields/get');
        const data = await response.json();

        if (data.status === 'success' && data.blocks.length > 0) {
            // Clear existing fields only when new ones are ready
            clearFieldBlocks();
            renderFieldBlocks(data.blocks);
        }
    } catch (error) {
        console.error('Error loading field blocks:', error);
    }
}

function renderFieldBlocks(blocks) {
    const container = document.getElementById('dynamic-fields-container');
    if (!container) return;

    container.innerHTML = '';

    blocks.forEach(block => {
        const blockElement = createBlockElement(block);
        container.appendChild(blockElement);
    });
}

function createBlockElement(block) {
    const blockDiv = document.createElement('div');
    blockDiv.className = `field-block field-block-${block.background}`;
    blockDiv.id = block.block_id;

    // Hide block if marked as hidden
    if (block.hidden) {
        blockDiv.style.display = 'none';
    }

    // Add title if exists
    if (block.title) {
        const titleDiv = document.createElement('div');
        titleDiv.className = 'field-block-title';
        titleDiv.textContent = block.title;
        blockDiv.appendChild(titleDiv);
    }

    // Add fields
    const fieldsContainer = document.createElement('div');
    fieldsContainer.className = 'field-block-content';

    block.fields.forEach(field => {
        const fieldElement = createFieldElement(field);
        fieldsContainer.appendChild(fieldElement);
    });

    blockDiv.appendChild(fieldsContainer);

    // Add send button if block has inputs
    if (block.has_inputs) {
        const buttonDiv = document.createElement('div');
        buttonDiv.className = 'field-block-actions';

        const button = document.createElement('button');
        button.className = 'btn btn-primary field-submit-btn';
        button.textContent = block.submit_button_text || 'Send & Continue';

        // Use custom endpoint if specified
        if (block.submit_endpoint) {
            button.onclick = () => submitFormData(block.block_id, block.submit_endpoint);
        } else {
            button.onclick = () => submitBlockData(block.block_id);
        }

        buttonDiv.appendChild(button);
        blockDiv.appendChild(buttonDiv);
    }

    return blockDiv;
}

function createFieldElement(field) {
    const fieldDiv = document.createElement('div');
    fieldDiv.className = `field field-type-${field.field_type}`;

    switch(field.field_type) {
        case 'markdown':
            fieldDiv.innerHTML = formatMarkdownToHTML(field.content);
            break;

        case 'input':
            if (field.label) {
                const label = document.createElement('label');
                label.htmlFor = field.field_id;
                label.textContent = field.label;
                fieldDiv.appendChild(label);
            }

            const input = document.createElement('input');
            input.type = field.input_type || 'text';
            input.id = field.field_id;
            input.name = field.field_id;
            input.placeholder = field.placeholder || '';
            input.value = field.value || '';
            if (field.required) input.required = true;

            // Hide the field if it's a hidden input
            if (field.input_type === 'hidden') {
                fieldDiv.style.display = 'none';
            }

            fieldDiv.appendChild(input);
            break;

        case 'textarea':
            const textLabel = document.createElement('label');
            textLabel.htmlFor = field.field_id;
            textLabel.textContent = field.label;
            fieldDiv.appendChild(textLabel);

            const textarea = document.createElement('textarea');
            textarea.id = field.field_id;
            textarea.name = field.field_id;
            textarea.placeholder = field.placeholder || '';
            textarea.rows = field.rows || 4;
            fieldDiv.appendChild(textarea);
            break;

        case 'button':
            const button = document.createElement('button');
            button.className = 'btn btn-secondary';
            button.textContent = field.text;
            button.onclick = () => handleFieldButton(field.field_id, field.action);
            fieldDiv.appendChild(button);
            break;

        case 'custom_html':
            fieldDiv.innerHTML = field.html_content;
            break;
    }

    return fieldDiv;
}

function handleFieldButton(buttonId, action) {
    if (action === 'expand') {
        // Show the feedback form
        const feedbackForm = document.getElementById('feedback_form');
        if (feedbackForm) {
            feedbackForm.style.display = 'block';
            // Smooth scroll to form
            feedbackForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

async function submitFormData(blockId, endpoint) {
    const block = document.getElementById(blockId);
    if (!block) return;

    // Collect all input values including textarea
    const inputs = block.querySelectorAll('input, textarea');
    const fieldData = {};

    inputs.forEach(input => {
        if (input.type !== 'checkbox') {
            fieldData[input.id || input.name] = input.value;
        }
    });

    // Find the submit button
    const button = block.querySelector('.field-submit-btn');
    if (button) {
        button.disabled = true;
        button.textContent = 'Sending...';
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(fieldData)
        });

        const result = await response.json();

        if (result.status === 'success') {
            // Replace form with thank you message
            const blockContent = block.querySelector('.field-block-content');
            if (blockContent) {
                blockContent.innerHTML = formatMarkdownToHTML('### ✅ ' + result.message);
            }
            // Hide submit button
            const actions = block.querySelector('.field-block-actions');
            if (actions) actions.style.display = 'none';
        }

    } catch (error) {
        console.error('Error submitting form:', error);
        alert('Failed to submit feedback. Please try again.');
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = 'Send Feedback';
        }
    }
}

async function submitBlockData(blockId) {
    const block = document.getElementById(blockId);
    if (!block) return;

    // Collect all input values
    const inputs = block.querySelectorAll('input, textarea');
    const checkboxes = block.querySelectorAll('input[type="checkbox"]:checked');
    const fieldData = {};

    inputs.forEach(input => {
        if (input.type !== 'checkbox') {
            fieldData[input.id || input.name] = input.value;
        }
    });

    // Handle checkboxes if any exist in custom HTML
    if (checkboxes.length > 0) {
        const checkboxValues = {};
        checkboxes.forEach(cb => {
            const name = cb.name;
            if (!checkboxValues[name]) {
                checkboxValues[name] = [];
            }
            checkboxValues[name].push(cb.value);
        });
        Object.assign(fieldData, checkboxValues);
    }

    // Find the submit button
    const button = block.querySelector('.field-submit-btn');
    if (button) {
        button.disabled = true;
        button.textContent = 'Sending...';
    }

    try {
        const response = await fetch('/api/fields/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                block_id: blockId,
                fields: fieldData
            })
        });

        const result = await response.json();
        console.log('Field data submitted:', result);

    } catch (error) {
        console.error('Error submitting field data:', error);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = 'Sent!';
        }
    }
}

// ========== TEASER CHAT FUNCTIONS ==========
// Global variable to store session ID for handoff to full workspace
let teaserSessionId = null;
let waitingForWorkspaceName = false;

async function sendTeaserMessage() {
    const input = document.getElementById('teaserProductInput');
    const message = input.value.trim();

    if (!message) {
        // Highlight the input field
        input.style.borderColor = '#ef4444';
        setTimeout(() => {
            input.style.borderColor = '';
        }, 1000);
        return;
    }

    // Disable input and button
    const sendBtn = document.getElementById('teaserSendBtn');
    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    // Add user message to chat
    addTeaserMessage('user', message);
    input.value = '';

    // Check if we're waiting for workspace name
    if (waitingForWorkspaceName) {
        // User provided workspace name, create workspace
        await createWorkspaceFromSession(message);
        return;
    }

    try {
        let response, data;

        // If we already have a session, continue the conversation
        if (teaserSessionId) {
            response = await fetch('/api/develope/respond', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: teaserSessionId,
                    message: message
                })
            });
        } else {
            // First message - start new conversation
            response = await fetch('/api/develope/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({initial_input: message})
            });
        }

        data = await response.json();

        if (data.error) {
            addTeaserMessage('assistant', 'Error: ' + data.error);
        } else {
            // Store session ID for handoff (only on first message)
            if (data.session_id) {
                teaserSessionId = data.session_id;
            }

            // Add AI response
            addTeaserMessage('assistant', data.message);

            // Check if AI has enough info to generate report
            if (data.complete) {
                // AI is ready! Check if user is logged in
                const user = getCurrentUser();

                if (user) {
                    // User is logged in, prepare for product name
                    waitingForWorkspaceName = true;

                    // Add a clear follow-up prompt for product name
                    addTeaserMessage('assistant', 'What would you like to name your product?');

                    // Update UI state
                    sendBtn.textContent = 'Create';
                    input.placeholder = 'e.g., Wall Light 5W';
                } else {
                    // User not logged in, show sign in prompt
                    showSignInPromptInChat();
                }
            } else {
                // AI needs more info, keep chatting on landing page
                // Change button text to "Send" for follow-up messages
                sendBtn.textContent = 'Send';
            }
        }
    } catch (error) {
        console.error('Error:', error);
        addTeaserMessage('assistant', 'Sorry, something went wrong. Please try again.');
    } finally {
        // Re-enable input and button
        input.disabled = false;
        sendBtn.disabled = false;
        // Keep button text as "Send" if we have an active session or waiting for name
        if (!teaserSessionId && !waitingForWorkspaceName) {
            sendBtn.textContent = 'Start Chat';
        } else {
            sendBtn.textContent = waitingForWorkspaceName ? 'Create' : 'Send';
        }
    }
}

function addTeaserMessage(role, content) {
    const messagesDiv = document.getElementById('teaserChatMessages');
    const messageDiv = document.createElement('div');
    // Add both old and new classes for styling compatibility
    messageDiv.className = `teaser-message teaser-${role} ns-message ${role}`;

    const label = role === 'user' ? 'You' : 'NormScout AI';
    messageDiv.innerHTML = `<strong>${label}</strong><p>${content}</p>`;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/**
 * Show sign in prompt in the chat
 */
function showSignInPromptInChat() {
    // Add message prompting sign-in
    addTeaserMessage('assistant', 'To save your workspace and continue the analysis, please sign in.');

    // Show sign in button in the continue container
    const continueContainer = document.getElementById('teaserContinueContainer');
    continueContainer.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <button class="btn btn-accent btn-large" onclick="showLoginModal()">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style="margin-right: 8px;">
                    <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
                Sign In to Continue
            </button>
        </div>
    `;
    continueContainer.style.display = 'block';

    // Hide input container
    document.getElementById('teaserInputContainer').style.display = 'none';
}

/**
 * Create workspace from teaser session
 */
async function createWorkspaceFromSession(productName) {
    if (!teaserSessionId) {
        addTeaserMessage('assistant', 'Sorry, I couldn\'t find your session. Please refresh and try again.');
        waitingForWorkspaceName = false;
        const sendBtn = document.getElementById('teaserSendBtn');
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
        return;
    }

    // Get UI elements
    const inputContainer = document.getElementById('teaserInputContainer');
    const progressBtn = document.getElementById('teaserProgressBtn');
    const progressBar = document.getElementById('teaserProgressBar');
    const progressText = document.getElementById('teaserProgressText');

    try {
        // Step 1: Run the norm analysis
        addTeaserMessage('assistant', 'Analyzing your product for compliance requirements...');

        // Hide input, show progress button with /develope styling
        if (inputContainer) inputContainer.style.display = 'none';
        if (progressBtn) {
            progressBtn.style.display = 'block';
            progressBtn.disabled = true;
            progressBtn.classList.add('analyzing');
        }
        if (progressText) progressText.textContent = 'Starting analysis...';
        if (progressBar) progressBar.style.width = '0%';

        // Connect to analysis stream
        const eventSource = new EventSource(`/api/develope/analyze-stream?session_id=${teaserSessionId}`);

        let analysisComplete = false;
        let analysisResults = null;

        await new Promise((resolve, reject) => {
            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.phase === 'analyzing') {
                    // Update the beautiful animated progress bar (like /develope)!
                    const progressPercent = Math.round((data.progress / data.total) * 100);
                    if (progressBar) progressBar.style.width = `${progressPercent}%`;
                    if (progressText) progressText.textContent = `Analyzing compliance norms... ${progressPercent}%`;
                }
                else if (data.phase === 'complete') {
                    // Analysis done!
                    analysisComplete = true;
                    analysisResults = data;
                    eventSource.close();
                    if (progressBar) progressBar.style.width = '100%';
                    if (progressText) progressText.textContent = 'Analysis complete!';
                    resolve();
                }
                else if (data.phase === 'error') {
                    eventSource.close();
                    reject(new Error(data.error || 'Analysis failed'));
                }
            };

            eventSource.onerror = function(error) {
                eventSource.close();
                reject(new Error('Connection to analysis service failed'));
            };
        });

        if (!analysisComplete) {
            throw new Error('Analysis did not complete successfully');
        }

        // Step 2: Create workspace with analysis results
        addTeaserMessage('assistant', `Found ${analysisResults.total_norms} relevant compliance norms! Creating your project...`);

        if (progressText) progressText.textContent = 'Creating project...';

        // Get session data (now includes analysis results)
        const sessionResponse = await fetch(`/api/develope/session/${teaserSessionId}`, {
            credentials: 'include'
        });

        if (!sessionResponse.ok) {
            const errorData = await sessionResponse.json().catch(() => ({}));
            throw new Error(errorData.error || 'Failed to get session data');
        }

        const sessionData = await sessionResponse.json();

        // Create workspace with REAL analysis data
        const response = await fetch('/api/workspaces/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({
                name: productName,
                product_description: sessionData.product_description || sessionData.history?.[0]?.content || productName,
                matched_norms: sessionData.matched_norms || [],
                all_results: sessionData.all_norm_results || {}
            })
        });

        const data = await response.json();

        if (!response.ok) {
            if (data.limit_exceeded) {
                addTeaserMessage('assistant', `Sorry, ${data.error}`);
                // Reset UI
                if (progressBtn) progressBtn.style.display = 'none';
                if (inputContainer) inputContainer.style.display = 'flex';
                waitingForWorkspaceName = false;
                return;
            }
            throw new Error(data.error || 'Failed to create project');
        }

        // Success! Show confirmation and redirect
        addTeaserMessage('assistant', `Perfect! "${productName}" has been created with ${analysisResults.total_norms} compliance norms. Redirecting...`);

        if (progressText) progressText.textContent = 'Complete! Redirecting...';

        // Redirect to workspace after a short delay
        setTimeout(() => {
            window.location.href = `/workspace/${data.workspace.id}`;
        }, 1500);

    } catch (error) {
        console.error('Error creating project:', error);
        addTeaserMessage('assistant', `Oops! Something went wrong: ${error.message}. Please try again.`);

        // Reset UI state (like /develope)
        if (progressBtn) {
            progressBtn.style.display = 'none';
            progressBtn.classList.remove('analyzing');
            progressBtn.disabled = false;
        }
        if (progressBar) progressBar.style.width = '0%';
        if (progressText) progressText.textContent = 'Analyzing...';
        if (inputContainer) inputContainer.style.display = 'flex';
        waitingForWorkspaceName = false;
    }
}

// Legacy functions removed - now using chat-based approach

// Allow Enter key to send message in teaser
document.addEventListener('DOMContentLoaded', function() {
    const teaserInput = document.getElementById('teaserProductInput');
    if (teaserInput) {
        teaserInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTeaserMessage();
            }
        });
    }
});