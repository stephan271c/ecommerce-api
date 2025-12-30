/**
 * E-Commerce Frontend - JavaScript
 * Handles authentication, API calls, and dynamic interactions
 */

(() => {
  'use strict';

  // ============================================
  // Token Management (cookies handled by browser)
  // ============================================

  const TokenManager = {
    USER_KEY: 'current_user',

    // Note: Token is now stored in HttpOnly cookie, managed by browser
    // We only cache user info in localStorage for display purposes

    getUser() {
      try {
        const user = localStorage.getItem(this.USER_KEY);
        return user ? JSON.parse(user) : null;
      } catch (e) {
        // Handle corrupted localStorage data
        this.removeUserCache();
        return null;
      }
    },

    setUser(user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    removeUserCache() {
      localStorage.removeItem(this.USER_KEY);
    },

    isAuthenticated() {
      // With HttpOnly cookies, we can't check the token directly
      // We rely on cached user info as a hint (actual auth is verified server-side)
      return !!this.getUser();
    }
  };

  // ============================================
  // API Client
  // ============================================

  const API = {
    baseUrl: '',

    async request(endpoint, options = {}) {
      const config = {
        credentials: 'include', // Include cookies in requests
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      };

      try {
        const response = await fetch(`${this.baseUrl}${endpoint}`, config);

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.indexOf('application/json') !== -1) {
          data = await response.json();
        } else {
          data = { message: await response.text() };
        }

        if (!response.ok) {
          throw { status: response.status, data };
        }

        return data;
      } catch (error) {
        // Handle network errors (offline, DNS failure, etc.)
        if (error instanceof TypeError) {
          showFlash('Network error. Please check your connection.', 'error');
          throw { status: 0, data: { message: 'Network error' } };
        }

        if (error.status === 401) {
          TokenManager.removeUserCache();
          showFlash('Session expired. Please login again.', 'error');
          setTimeout(() => window.location.href = '/login', 1500);
        }
        throw error;
      }
    },

    get(endpoint) {
      return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, data) {
      return this.request(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
      });
    },

    put(endpoint, data) {
      return this.request(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    },

    delete(endpoint) {
      return this.request(endpoint, { method: 'DELETE' });
    },

    // Special method for form-urlencoded (OAuth2 login)
    async postForm(endpoint, formData) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams(formData)
      });

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data;
      if (contentType && contentType.indexOf('application/json') !== -1) {
        data = await response.json();
      } else {
        data = { message: await response.text() };
      }

      if (!response.ok) {
        throw { status: response.status, data };
      }

      return data;
    }
  };

  // ============================================
  // Flash Messages (XSS-safe)
  // ============================================

  function showFlash(message, type = 'info') {
    // Remove existing flash messages
    const existing = document.querySelector('.flash-message');
    if (existing) existing.remove();

    const flash = document.createElement('div');
    flash.className = `alert alert-${type} flash-message`;
    flash.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);z-index:1000;min-width:300px;max-width:90%;animation:slideDown 0.3s ease;';

    // Use textContent to prevent XSS (safe DOM API)
    const textSpan = document.createElement('span');
    textSpan.textContent = message;
    flash.appendChild(textSpan);

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;'; // Safe - hardcoded value
    closeBtn.style.cssText = 'background:none;border:none;color:inherit;cursor:pointer;margin-left:auto;font-size:1.2rem;';
    closeBtn.addEventListener('click', () => flash.remove());
    flash.appendChild(closeBtn);

    document.body.appendChild(flash);

    // Auto-remove after 5 seconds
    setTimeout(() => flash.remove(), 5000);
  }

  // Add animation styles
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideDown {
      from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
      to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
  `;
  document.head.appendChild(style);

  // ============================================
  // Form Helpers
  // ============================================

  function setFormDisabled(form, disabled) {
    const elements = form.querySelectorAll('input, button, textarea, select');
    elements.forEach(el => el.disabled = disabled);
  }

  function getListingFormData(form) {
    return {
      title: form.title.value,
      description: form.description.value,
      price: parseFloat(form.price.value),
      category: form.category.value,
      is_active: form.is_active?.checked ?? true
    };
  }

  // ============================================
  // Auth Functions
  // ============================================

  async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    try {
      setFormDisabled(form, true);
      submitBtn.textContent = 'Logging in...';

      await API.postForm('/v1/auth/login', {
        username: form.username.value,
        password: form.password.value
      });

      // Fetch user profile and cache it
      const user = await API.get('/v1/users/me');
      TokenManager.setUser(user);

      showFlash('Login successful!', 'success');
      setTimeout(() => window.location.href = '/', 1000);

    } catch (error) {
      showFlash(error.data?.message || 'Invalid credentials', 'error');
    } finally {
      setFormDisabled(form, false);
      submitBtn.textContent = originalText;
    }
  }

  async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    // Validate password match
    if (form.password.value !== form.confirm_password.value) {
      showFlash('Passwords do not match', 'error');
      return;
    }

    try {
      setFormDisabled(form, true);
      submitBtn.textContent = 'Creating account...';

      await API.post('/v1/auth/register', {
        email: form.email.value,
        username: form.username.value,
        password: form.password.value
      });

      showFlash('Account created! Please login.', 'success');
      setTimeout(() => window.location.href = '/login', 1500);

    } catch (error) {
      const message = error.data?.message || error.data?.detail?.[0]?.msg || 'Registration failed';
      showFlash(message, 'error');
    } finally {
      setFormDisabled(form, false);
      submitBtn.textContent = originalText;
    }
  }

  async function handleLogout() {
    try {
      await API.post('/v1/auth/logout', {});
    } catch (error) {
      // Logout should succeed even if API call fails
    }
    TokenManager.removeUserCache();
    showFlash('Logged out successfully', 'success');
    setTimeout(() => window.location.href = '/', 1000);
  }

  // ============================================
  // Listing Functions
  // ============================================

  async function handleCreateListing(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    try {
      setFormDisabled(form, true);
      submitBtn.textContent = 'Creating...';

      const data = getListingFormData(form);
      const listing = await API.post('/v1/listings', data);
      showFlash('Listing created successfully!', 'success');
      setTimeout(() => window.location.href = `/listings/${listing.id}`, 1000);

    } catch (error) {
      showFlash(error.data?.message || 'Failed to create listing', 'error');
    } finally {
      setFormDisabled(form, false);
      submitBtn.textContent = originalText;
    }
  }

  async function handleUpdateListing(event, listingId) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    try {
      setFormDisabled(form, true);
      submitBtn.textContent = 'Saving...';

      const data = getListingFormData(form);
      await API.put(`/v1/listings/${listingId}`, data);
      showFlash('Listing updated successfully!', 'success');
      setTimeout(() => window.location.href = `/listings/${listingId}`, 1000);

    } catch (error) {
      showFlash(error.data?.message || 'Failed to update listing', 'error');
    } finally {
      setFormDisabled(form, false);
      submitBtn.textContent = originalText;
    }
  }

  async function handleDeleteListing(listingId) {
    if (!confirm('Are you sure you want to delete this listing?')) return;

    try {
      await API.delete(`/v1/listings/${listingId}`);
      showFlash('Listing deleted successfully!', 'success');
      setTimeout(() => window.location.href = '/listings', 1000);
    } catch (error) {
      showFlash(error.data?.message || 'Failed to delete listing', 'error');
    }
  }

  // ============================================
  // Profile Functions
  // ============================================

  async function handleUpdateProfile(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    const userId = form.dataset.userId;

    try {
      setFormDisabled(form, true);
      submitBtn.textContent = 'Saving...';

      const data = {};
      if (form.username.value) data.username = form.username.value;
      if (form.email.value) data.email = form.email.value;

      const user = await API.put(`/v1/users/${userId}`, data);
      TokenManager.setUser(user);
      showFlash('Profile updated successfully!', 'success');

    } catch (error) {
      showFlash(error.data?.message || 'Failed to update profile', 'error');
    } finally {
      setFormDisabled(form, false);
      submitBtn.textContent = originalText;
    }
  }

  // ============================================
  // UI Updates
  // ============================================

  function updateNavbar() {
    const authNav = document.querySelector('.navbar-auth');
    if (!authNav) return;

    const user = TokenManager.getUser();
    const isAuth = TokenManager.isAuthenticated();

    // Clear existing content safely
    authNav.innerHTML = '';

    if (isAuth && user) {
      const profileLink = document.createElement('a');
      profileLink.href = '/profile';
      profileLink.className = 'btn btn-secondary btn-sm';
      profileLink.textContent = user.username;
      authNav.appendChild(profileLink);

      const logoutBtn = document.createElement('button');
      logoutBtn.className = 'btn btn-secondary btn-sm';
      logoutBtn.textContent = 'Logout';
      logoutBtn.addEventListener('click', handleLogout);
      authNav.appendChild(logoutBtn);
    } else {
      const loginLink = document.createElement('a');
      loginLink.href = '/login';
      loginLink.className = 'btn btn-secondary btn-sm';
      loginLink.textContent = 'Login';
      authNav.appendChild(loginLink);

      const signupLink = document.createElement('a');
      signupLink.href = '/register';
      signupLink.className = 'btn btn-primary btn-sm';
      signupLink.textContent = 'Sign Up';
      authNav.appendChild(signupLink);
    }

    // Reveal navbar auth section (was hidden by CSS initially)
    authNav.classList.add('ready');
  }

  // ============================================
  // Initialize
  // ============================================

  document.addEventListener('DOMContentLoaded', () => {
    updateNavbar();

    // Auto-hide flash messages from server
    const flashes = document.querySelectorAll('.alert');
    flashes.forEach(flash => {
      setTimeout(() => flash.remove(), 5000);
    });

    // Attach form handlers
    const loginForm = document.getElementById('login-form');
    if (loginForm) loginForm.addEventListener('submit', handleLogin);

    const registerForm = document.getElementById('register-form');
    if (registerForm) registerForm.addEventListener('submit', handleRegister);

    const createListingForm = document.getElementById('create-listing-form');
    if (createListingForm) createListingForm.addEventListener('submit', handleCreateListing);

    const updateListingForm = document.getElementById('update-listing-form');
    if (updateListingForm) {
      updateListingForm.addEventListener('submit', (e) => {
        const listingId = updateListingForm.dataset.listingId;
        handleUpdateListing(e, listingId);
      });
    }

    const deleteListingBtn = document.getElementById('delete-listing-btn');
    if (deleteListingBtn) {
      deleteListingBtn.addEventListener('click', () => {
        const listingId = deleteListingBtn.dataset.listingId;
        handleDeleteListing(listingId);
      });
    }

    const profileForm = document.getElementById('profile-form');
    if (profileForm) profileForm.addEventListener('submit', handleUpdateProfile);
  });

  // Expose APIs for inline handlers and template scripts
  window.handleLogout = handleLogout;
  window.TokenManager = TokenManager;
  window.API = API;
  window.showFlash = showFlash;
})();
