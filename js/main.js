window.addEventListener('DOMContentLoaded', async () => {
  // --- Configuration Variables (will be loaded from config.json) ---
  let appConfig = {
    appName: "Classic News",
    baseCategories: [
      'Politics', 'Science', 'Health', 'Sports', 'India', 'World',
      'Business', 'Tech', 'Travel', 'Art', 'Environment', 'Education',
      'Food', 'Fashion', 'Automotive', 'Space', 'Culture', 'Lifestyle', 'Gaming'
    ],
    weatherApi: {
      name: "WeatherAPI.com",
      key: "YOUR_WEATHERAPI_API_KEY",
      baseUrl: "https://api.weatherapi.com/v1/current.json",
      websiteUrl: "https://www.weatherapi.com/"
    }
  };

  // --- Load Configuration from config.json ---
  try {
    const response = await fetch('config.json');
    if (!response.ok) {
      console.warn('config.json not found or failed to load. Using default configuration.');
    } else {
      const customConfig = await response.json();
      // Merge default config with custom config
      appConfig = {
        ...appConfig,
        ...customConfig,
        weatherApi: { ...appConfig.weatherApi, ...(customConfig.weatherApi || {}) }
      };
      console.log('Configuration loaded:', appConfig);
    }
  } catch (error) {
    console.error('Error loading config.json:', error);
    console.warn('Using default configuration due to error.');
  }

  // Apply app name from config to HTML elements
  document.getElementById('app-title').textContent = appConfig.appName;
  document.getElementById('app-header-name').textContent = appConfig.appName;
  document.getElementById('app-footer-name').textContent = `© 2025 ${appConfig.appName}. All rights reserved.`;


  // Get the loader element
  const loader = document.getElementById('loader');
  // Hide the loader after a delay and show the main content
  setTimeout(() => {
    loader.style.display = 'none';
    document.getElementById('main-content').style.display = '';
  }, 1200); // 1.2 second delay

  // Categories: Breaking News, then others, then All (from config)
  const categories = ['Breaking News', ...appConfig.baseCategories, 'All'];
  const tilesContainer = document.getElementById('categories-tiles');
  let selectedCategory = 'Breaking News'; // Default selected category
  let allNews = []; // Array to hold all fetched news articles
  let currentPage = 1; // Current page for pagination
  const newsPerPage = 9; // Number of news cards to display per page

  // --- Cookie Consent Elements ---
  const cookieConsentBanner = document.getElementById('cookie-consent-banner');
  const acceptCookiesBtn = document.getElementById('accept-cookies-btn');
  let cookiesAccepted = false; // Flag to track cookie consent (now refers to localStorage consent)

  // --- Weather Widget Elements ---
  const weatherWidget = document.getElementById('weather-widget');
  const weatherIcon = document.getElementById('weather-icon');
  const weatherLocation = document.getElementById('weather-location');
  const weatherTemperature = document.getElementById('weather-temperature');
  const weatherDescription = document.getElementById('weather-description');

  let userLatitude = null;
  let userLongitude = null;
  let currentCityName = ''; // Variable to store the fetched city name

  // --- Local Storage Utility Functions (replacing cookie functions) ---
  function setLocalStorage(name, value) {
    try {
      localStorage.setItem(name, value);
    } catch (e) {
      console.error("Error setting localStorage item:", name, e);
    }
  }

  function getLocalStorage(name) {
    try {
      return localStorage.getItem(name);
    } catch (e) {
      console.error("Error getting localStorage item:", name, e);
      return null;
    }
  }

  function checkCookieConsent() {
    // Check localStorage for consent
    if (getLocalStorage('cookies_accepted') === 'true') {
      cookiesAccepted = true;
      cookieConsentBanner.classList.remove('show');
    } else {
      cookieConsentBanner.classList.add('show');
    }
  }

  function acceptCookies() {
    setLocalStorage('cookies_accepted', 'true'); // Consent stored in localStorage
    cookiesAccepted = true;
    cookieConsentBanner.classList.remove('show');
  }

  // --- Visited News Tracking (now using Local Storage) ---
  function getVisitedNewsIds() {
    if (!cookiesAccepted) return [];
    const visitedIdsJson = getLocalStorage('visited_news_ids');
    try {
      return visitedIdsJson ? JSON.parse(visitedIdsJson) : [];
    } catch (e) {
      console.error("Error parsing visited_news_ids from localStorage:", e);
      return [];
    }
  }

  function addVisitedNewsId(uniqueId) {
    if (!cookiesAccepted) return;
    let visitedIds = getVisitedNewsIds();
    if (!visitedIds.includes(uniqueId)) {
      visitedIds.push(uniqueId);
      // Keep the list from growing indefinitely, e.g., last 100 visited
      if (visitedIds.length > 100) {
        visitedIds = visitedIds.slice(-100);
      }
      setLocalStorage('visited_news_ids', JSON.stringify(visitedIds)); // Store in localStorage
    }
  }

  // --- Category Icon Function ---
  function getCategoryIcon(category) {
    switch (category) {
      case 'Politics': return '🏛️';
      case 'Science': return '🔬';
      case 'Health': return '❤️';
      case 'Sports': return '🏅';
      case 'India': return '🇮🇳';
      case 'World': return '🌍';
      case 'Business': return '📈';
      case 'Tech': return '💻';
      case 'Travel': return '✈️';
      case 'Art': return '🎨';
      case 'Environment': return '🌳';
      case 'Education': return '📚';
      case 'Food': return '🍔';
      case 'Fashion': return '👗';
      case 'Automotive': return '🚗';
      case 'Space': return '🚀';
      case 'Culture': return '�';
      case 'Lifestyle': return '🧘';
      case 'Gaming': return '🎮';
      case 'Breaking News': return '⚡';
      case 'All': return '📰';
      default: return '✨';
    }
  }

  // --- Weather Widget Functions ---
  function getWeatherEmoji(conditionText) {
    const lowerText = conditionText.toLowerCase();
    if (lowerText.includes('sun') || lowerText.includes('clear')) return '☀️';
    if (lowerText.includes('cloud') || lowerText.includes('overcast')) return '☁️';
    if (lowerText.includes('rain') || lowerText.includes('drizzle')) return '🌧️';
    if (lowerText.includes('thunder')) return '⛈️';
    if (lowerText.includes('snow') || lowerText.includes('sleet')) return '❄️';
    if (lowerText.includes('mist') || lowerText.includes('fog')) return '🌫️';
    if (lowerText.includes('partly cloudy')) return '🌤️';
    return '🌡️'; // Default thermometer emoji
  }

  async function fetchWeatherData(lat, lon) {
    const weatherApiKey = appConfig.weatherApi.key;
    const weatherBaseUrl = appConfig.weatherApi.baseUrl;

    if (!weatherApiKey || weatherApiKey === 'YOUR_WEATHERAPI_API_KEY') {
        console.error(`Weather API key is not set. Please replace 'YOUR_WEATHERAPI_API_KEY' in config.json for ${appConfig.weatherApi.name}.`);
        weatherLocation.textContent = 'API Key Missing';
        weatherTemperature.textContent = '';
        weatherDescription.textContent = 'Weather unavailable';
        weatherIcon.textContent = '⚠️';
        return;
    }

    const url = `${weatherBaseUrl}?key=${weatherApiKey}&q=${lat},${lon}`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! Status: ${response.status}. Message: ${errorText}`);
      }
      const data = await response.json();
      updateWeatherWidget(data);
    } catch (error) {
      console.error('Error fetching weather data:', error.message);
      weatherLocation.textContent = 'Weather Error';
      weatherTemperature.textContent = '';
      weatherDescription.textContent = 'Failed to load';
      weatherIcon.textContent = '❌';
    }
  }

  function updateWeatherWidget(data) {
    if (data && data.location && data.current && data.current.condition) {
      currentCityName = data.location.name; // Store the city name
      weatherLocation.textContent = currentCityName;
      weatherTemperature.textContent = `${Math.round(data.current.temp_c)}°C`; // temp_c for Celsius
      weatherDescription.textContent = data.current.condition.text;
      weatherIcon.textContent = getWeatherEmoji(data.current.condition.text); // Use condition text for emoji
    } else {
      weatherLocation.textContent = 'N/A';
      weatherTemperature.textContent = '';
      weatherDescription.textContent = 'No data';
      weatherIcon.textContent = '❓';
      currentCityName = ''; // Clear city name if no data
    }
  }

  function getGeolocationAndWeather() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          userLatitude = position.coords.latitude;
          userLongitude = position.coords.longitude;
          fetchWeatherData(userLatitude, userLongitude);
        },
        (error) => {
          console.error(`Geolocation error (${error.code}): ${error.message}`);
          let errorMessage = 'Location Denied';
          if (error.code === error.PERMISSION_DENIED) {
            errorMessage = 'Location access denied.';
          } else if (error.code === error.POSITION_UNAVAILABLE) {
            errorMessage = 'Location information unavailable.';
          } else if (error.code === error.TIMEOUT) {
            errorMessage = 'Location request timed out.';
          }
          weatherLocation.textContent = errorMessage;
          weatherTemperature.textContent = '';
          weatherDescription.textContent = 'Weather unavailable';
          weatherIcon.textContent = '🚫';
          currentCityName = ''; // Clear city name on error
        }
      );
    } else {
      console.error('Geolocation is not supported by this browser.');
      weatherLocation.textContent = 'Geo Not Supported';
      weatherTemperature.textContent = '';
      weatherDescription.textContent = 'Weather unavailable';
      weatherIcon.textContent = '⛔';
      currentCityName = ''; // Clear city name if not supported
    }
  }

  // Initial fetch of weather data and set up refresh
  getGeolocationAndWeather();
  // Refresh weather every 5 minutes (300,000 milliseconds)
  setInterval(() => {
    if (userLatitude && userLongitude) {
      fetchWeatherData(userLatitude, userLongitude);
    } else {
      getGeolocationAndWeather(); // Try to get location again if not available
    }
  }, 300000); // 5 minutes

  // Make weather widget clickable to open weather website for the specific location
  weatherWidget.addEventListener('click', () => {
    if (currentCityName) {
      const encodedCity = encodeURIComponent(currentCityName);
      window.open(`https://www.google.com/search?q=weather+in+${encodedCity}`, '_blank');
    } else if (appConfig.weatherApi.websiteUrl) {
      window.open(appConfig.weatherApi.websiteUrl, '_blank'); // Fallback to API provider's site
    } else {
      window.open('https://www.google.com/search?q=weather', '_blank'); // Generic weather search
    }
  });

  // --- Category Tile Rendering ---
  function renderTiles() {
    tilesContainer.innerHTML = ''; // Clear existing tiles
    categories.forEach(category => {
      const tileWrapper = document.createElement('div');
      tileWrapper.className = `relative category-card-3d flex-shrink-0 w-36 h-28 rounded-xl shadow-md
        flex flex-col items-center justify-center font-semibold text-base cursor-pointer transition-all duration-300 ease-in-out
        ${selectedCategory === category ? 'selected' : ''}
      `;

      const innerCard = document.createElement('div');
      innerCard.className = `inner-card w-full h-full flex flex-col items-center justify-center p-2 rounded-xl
        bg-gradient-to-br from-blue-600 to-blue-800 text-white
      `;

      if (selectedCategory === category) {
        const checkmarkSvg = `
          <svg class="absolute top-1 right-1 w-5 h-5 text-white animate-fade-in" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 10 001.414 0l4-4z" clipRule="evenodd"></path>
          </svg>
        `;
        innerCard.innerHTML += checkmarkSvg;
      }

      innerCard.innerHTML += `<span class="text-3xl mb-1">${getCategoryIcon(category)}</span>`;
      innerCard.innerHTML += `<span class="text-sm text-center px-1">${category}</span>`;

      tileWrapper.appendChild(innerCard);

      tileWrapper.addEventListener('mousemove', (e) => {
        const card = e.currentTarget;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - (rect.left + rect.width / 2);
        const y = e.clientY - (rect.top + rect.height / 2);
        const rotateX = -y / 10;
        const rotateY = x / 10;
        card.style.setProperty('--rotateX', `${rotateX}deg`);
        card.style.setProperty('--rotateY', `${rotateY}deg`);
      });

      tileWrapper.addEventListener('mouseleave', (e) => {
        const card = e.currentTarget;
        card.style.setProperty('--rotateX', '0deg');
        card.style.setProperty('--Y', '0deg');
      });

      tileWrapper.addEventListener('click', () => {
        selectedCategory = category;
        currentPage = 1;
        renderTiles();
        renderNews();
        document.getElementById('header-categories-dropdown').classList.remove('open');
        document.getElementById('current-category-toggle').classList.remove('rotated');
        updateCurrentCategoryButton();
      });
      tilesContainer.appendChild(tileWrapper);
    });
  }

  // --- Pagination Rendering ---
  function renderPagination(totalPages) {
    function createPaginationElement() {
      const pagination = document.createElement('div');
      pagination.className = 'pagination';

      const leftArrow = document.createElement('button');
      leftArrow.className = 'pagination-arrow';
      leftArrow.innerHTML = '&#8592;';
      leftArrow.disabled = currentPage === 1;
      leftArrow.onclick = () => {
        if (currentPage > 1) {
          currentPage--;
          renderNews();
          createPaginationElement();
        }
      };
      pagination.appendChild(leftArrow);

      let start = Math.max(1, currentPage - 2);
      let end = Math.min(totalPages, currentPage + 2);
      if (currentPage <= 3) end = Math.min(5, totalPages);
      if (currentPage >= totalPages - 2) start = Math.max(1, totalPages - 4);

      for (let i = start; i <= end; i++) {
        const btn = document.createElement('button');
        btn.className = 'pagination-btn' + (i === currentPage ? ' active' : '');
        btn.textContent = i;
        btn.addEventListener('click', () => {
          currentPage = i;
          renderNews();
          createPaginationElement();
        });
        pagination.appendChild(btn);
      }

      const rightArrow = document.createElement('button');
      rightArrow.className = 'pagination-arrow';
      rightArrow.innerHTML = '&#8594;';
      rightArrow.disabled = currentPage === totalPages;
      rightArrow.onclick = () => {
        if (currentPage < totalPages) {
          currentPage++;
          renderNews();
          createPaginationElement();
        }
      };
      pagination.appendChild(rightArrow);

      const info = document.createElement('span');
      info.className = 'pagination-info';
      info.textContent = `Page ${currentPage} of ${totalPages}`;
      pagination.appendChild(info);

      return pagination;
    }

    const pagTop = document.getElementById('pagination-top');
    pagTop.innerHTML = '';
    pagTop.appendChild(createPaginationElement());
  }

  // --- News Card Rendering ---
  function renderNews() {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';
    let filtered = allNews;

    if (selectedCategory === 'Breaking News') {
      filtered = allNews.slice(0, 10);
    } else if (selectedCategory !== 'All') {
      filtered = allNews.filter(article =>
        (article.category && article.category.toLowerCase() === selectedCategory.toLowerCase())
      );
    }

    if (searchTerm) {
      filtered = filtered.filter(article =>
        (article.title && article.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (article.summary && article.summary.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    const totalPages = Math.ceil(filtered.length / newsPerPage) || 1;
    const startIdx = (currentPage - 1) * newsPerPage;
    const endIdx = startIdx + newsPerPage;
    const pageNews = filtered.slice(startIdx, endIdx);

    if (pageNews.length === 0) {
      grid.innerHTML = '<p class="text-center text-gray-600 dark:text-gray-400 col-span-full">No news found for this category or search term.</p>';
    } else {
      pageNews.forEach(article => {
        const title = highlight(article.title, searchTerm);
        const summary = highlight(article.summary, searchTerm);
        
        const locationDisplay = article.location ? `<span class="news-meta-separator">|</span> <span class="news-location-text">${article.location}</span>` : '';
        const dateTimeLocationStr = `
          <div class="news-meta-info">
            <span class="news-date-text">${article.date ? new Date(article.date).toLocaleDateString() : 'N/A'}</span>
            ${locationDisplay}
          </div>
        `;

        const card = document.createElement('div');
        card.className = 'news-card';
        card.innerHTML = `
          <img src="${article.img}" alt="${article.title}">
          <div class="p-4 flex-grow flex flex-col">
            ${dateTimeLocationStr}
            <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-2">${title}</h3>
            <p class="news-summary-justify text-gray-700 dark:text-gray-300 text-sm flex-grow">${summary}</p>
            <a class="read-more-btn mt-4 self-end bg-blue-600 text-white px-4 py-2 rounded-lg shadow-md hover:bg-blue-700 transition-colors opacity-0 group-hover:opacity-100"
              href="News/${encodeURIComponent(article.category)}/${encodeURIComponent(article.uniqueId)}.html" target="_blank" rel="noopener noreferrer">Read More</a>
          </div>
        `;
        grid.appendChild(card);

        // Add event listener to record visited news
        const readMoreBtn = card.querySelector('.read-more-btn');
        readMoreBtn.addEventListener('click', () => {
          if (cookiesAccepted) {
            addVisitedNewsId(article.uniqueId);
          } else {
            console.log("Cookies not accepted. Cannot record visited news.");
          }
        });
      });
    }
    renderPagination(totalPages);
  }

  // --- Breaking News Slider ---
  let breakingNews = [];
  let breakingIndex = 0;
  let breakingTimer = null;

  function renderBreakingNewsSlider() {
    const container = document.getElementById('breaking-news-content');
    const indicators = document.getElementById('breaking-indicators');

    container.innerHTML = '';

    const article = breakingNews[breakingIndex];
    const newSlideLink = document.createElement('a');
    newSlideLink.href = `News/${encodeURIComponent(article.category)}/${encodeURIComponent(article.uniqueId)}.html`;
    newSlideLink.target = "_blank";
    newSlideLink.rel = "noopener noreferrer";
    newSlideLink.className = 'breaking-news_slide slide-enter';

    // Add event listener to record visited news for slider
    newSlideLink.addEventListener('click', () => {
      if (cookiesAccepted) {
        addVisitedNewsId(article.uniqueId);
      } else {
        console.log("Cookies not accepted. Cannot record visited news from slider.");
      }
    });

    const locationDisplay = article.location ? `<span class="news-meta-separator">|</span> <span class="news-location-text">${article.location}</span>` : '';
    newSlideLink.innerHTML = `
      <img class="breaking-news-img" src="${article.img}" alt="${article.title}">
      <div class="breaking-news-info">
        <div class="news-meta-info">
          <span class="news-date-text">${article.date ? new Date(article.date).toLocaleDateString() : 'N/A'}</span>
          ${locationDisplay}
        </div>
        <h2>${article.title}</h2>
        <p class="breaking-news-summary">${article.summary}</p>
      </div>
    `;
    
    container.appendChild(newSlideLink);
    newSlideLink.offsetWidth;
    newSlideLink.classList.remove('slide-enter');

    indicators.innerHTML = '';
    breakingNews.forEach((_, idx) => {
      const dot = document.createElement('span');
      dot.className = 'breaking-indicator-dot' + (idx === breakingIndex ? ' active' : '');
      dot.addEventListener('click', () => {
        showBreakingNews(idx);
      });
      indicators.appendChild(dot);
    });
  }

  function showBreakingNews(idx) {
    breakingIndex = idx;
    renderBreakingNewsSlider();
    resetBreakingTimer();
  }

  function nextBreakingNews() {
    breakingIndex = (breakingIndex + 1) % breakingNews.length;
    renderBreakingNewsSlider();
    resetBreakingTimer();
  }

  function prevBreakingNews() {
    breakingIndex = (breakingIndex - 1 + breakingNews.length) % breakingNews.length;
    renderBreakingNewsSlider();
    resetBreakingTimer();
  }

  function resetBreakingTimer() {
    if (breakingTimer) clearTimeout(breakingTimer);
    breakingTimer = setTimeout(nextBreakingNews, 10000);
  }

  document.getElementById('breaking-next').onclick = nextBreakingNews;
  document.getElementById('breaking-prev').onclick = prevBreakingNews;

  // --- Fetch News Data ---
  fetch('Data/news.json')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(news => {
      allNews = news
        .filter(n => n.title && n.summary && n.img && n.date && n.category && n.uniqueId)
        .sort((a, b) => new Date(b.date) - new Date(a.date));
      
      breakingNews = allNews.slice(0, 7);
      renderBreakingNewsSlider();
      resetBreakingTimer();
      renderTiles();
      renderNews();
      updateCurrentCategoryButton();
    })
    .catch(error => {
      document.getElementById('news-grid').innerHTML = '<p class="text-center text-gray-600 dark:text-gray-400 col-span-full">Failed to load news.</p>';
      console.error('Error loading news:', error);
    });

  // --- Category Button Toggle ---
  const currentCategoryButton = document.getElementById('current-category-button');
  const headerCategoriesDropdown = document.getElementById('header-categories-dropdown');
  const currentCategoryToggle = document.getElementById('current-category-toggle');

  currentCategoryButton.addEventListener('click', () => {
    headerCategoriesDropdown.classList.toggle('open');
    currentCategoryToggle.classList.toggle('rotated');
  });

  function updateCurrentCategoryButton() {
    const currentCategoryText = document.getElementById('current-category-text');
    const currentCategoryIcon = document.getElementById('current-category-icon');
    currentCategoryText.textContent = selectedCategory;
    currentCategoryIcon.textContent = getCategoryIcon(selectedCategory);
  }

  // --- Search Functionality ---
  let searchTerm = '';
  const searchInput = document.getElementById('news-search');
  searchInput.addEventListener('input', (e) => {
    searchTerm = e.target.value.trim();
    currentPage = 1;
    renderNews();
  });

  function highlight(text, keyword) {
    if (!keyword || !text) return text;
    const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
  }

  // --- Theme & Color Switcher ---
  const themeToggle = document.getElementById('theme-toggle');
  const themeLabel = document.getElementById('theme-label');
  const colorSelect = document.getElementById('color-select');
  const root = document.documentElement;

  const primaryLight = "#2a5298";
  const primaryLightGradient = "linear-gradient(90deg, #1e3c72 0%, #2a5298 100%)";
  const backgroundLight = "#f0f2f5";
  const textLight = "#222";
  const cardBgLight = "#fff";

  const primaryDark = "#7ecbff";
  const primaryDarkGradient = "linear-gradient(90deg, #0f2027 0%, #2c5364 100%)";
  const backgroundDark = "#181c22";
  const textDark = "#f5f5f5";
  const cardBgDark = "#23272f";

  const accentRed = "#f44336";

  function setTheme(isDark) {
    if (isDark) {
      root.style.setProperty('--primary', primaryDark);
      root.style.setProperty('--primary-gradient', primaryDarkGradient);
      root.style.setProperty('--background', backgroundDark);
      root.style.setProperty('--text', textDark);
      root.style.setProperty('--card-bg', cardBgDark);
      root.style.setProperty('--shadow-color', 'rgba(0,0,0,0.3)');
      root.style.setProperty('--hover-shadow-color', 'rgba(0,0,0,0.4)');
      root.style.setProperty('--selected-shadow-color', 'rgba(244,67,54,0.3)');
    } else {
      root.style.setProperty('--primary', primaryLight);
      root.style.setProperty('--primary-gradient', primaryLightGradient);
      root.style.setProperty('--background', backgroundLight);
      root.style.setProperty('--text', textLight);
      root.style.setProperty('--card-bg', cardBgLight);
      root.style.setProperty('--shadow-color', 'rgba(0,0,0,0.1)');
      root.style.setProperty('--hover-shadow-color', 'rgba(0,0,0,0.18)');
      root.style.setProperty('--selected-shadow-color', 'rgba(244,67,54,0.18)');
    }
    root.style.setProperty('--red-500', accentRed);
    themeLabel.textContent = isDark ? 'Dark' : 'Light';
  }

  themeToggle.addEventListener('change', e => {
    setTheme(e.target.checked);
  });

  colorSelect.disabled = true;

  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  themeToggle.checked = prefersDark;
  setTheme(prefersDark);

  // --- Initialize Cookie Consent ---
  checkCookieConsent();
  acceptCookiesBtn.addEventListener('click', acceptCookies);
});
