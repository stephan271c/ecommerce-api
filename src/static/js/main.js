/**
 * E-Commerce Frontend - JavaScript
 * Handles authentication, API calls, and dynamic interactions
 */

// ============================================
// Token Management
// ============================================

const TokenManager = {
  TOKEN_KEY: 'access_token',
  USER_KEY: 'current_user',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  removeToken() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },

  getUser() {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) : null;
  },

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  isAuthenticated() {
    return !!this.getToken();
  }
};

// ============================================
// API Client
// ============================================

const API = {
  baseUrl: '',

  async request(endpoint, options = {}) {
    const token = TokenManager.getToken();

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config);
      const data = await response.json();

      if (!response.ok) {
        throw { status: response.status, data };
      }

      return data;
    } catch (error) {
      if (error.status === 401) {
        TokenManager.removeToken();
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
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(formData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw { status: response.status, data };
    }

    return data;
  }
};

// ============================================
// Flash Messages
// ============================================

function showFlash(message, type = 'info') {
  // Remove existing flash messages
  const existing = document.querySelector('.flash-message');
  if (existing) existing.remove();

  const flash = document.createElement('div');
  flash.className = `alert alert-${type} flash-message`;
  flash.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;color:inherit;cursor:pointer;margin-left:auto;font-size:1.2rem;">&times;</button>
    `;
  flash.style.cssText = 'position:fixed;top:80px;left:50%;transform:translateX(-50%);z-index:1000;min-width:300px;max-width:90%;animation:slideDown 0.3s ease;';

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
// Auth Functions
// ============================================

async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.textContent;

  try {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';

    const data = await API.postForm('/v1/auth/login', {
      username: form.username.value,
      password: form.password.value
    });

    TokenManager.setToken(data.access_token);

    // Fetch user profile
    const user = await API.get('/v1/users/me');
    TokenManager.setUser(user);

    showFlash('Login successful!', 'success');
    setTimeout(() => window.location.href = '/', 1000);

  } catch (error) {
    showFlash(error.data?.message || 'Invalid credentials', 'error');
  } finally {
    submitBtn.disabled = false;
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
    submitBtn.disabled = true;
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
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

function handleLogout() {
  TokenManager.removeToken();
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
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';

    const data = {
      title: form.title.value,
      description: form.description.value,
      price: parseFloat(form.price.value),
      category: form.category.value,
      is_active: form.is_active?.checked ?? true
    };

    const listing = await API.post('/v1/listings', data);
    showFlash('Listing created successfully!', 'success');
    setTimeout(() => window.location.href = `/listings/${listing.id}`, 1000);

  } catch (error) {
    showFlash(error.data?.message || 'Failed to create listing', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function handleUpdateListing(event, listingId) {
  event.preventDefault();
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.textContent;

  try {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    const data = {
      title: form.title.value,
      description: form.description.value,
      price: parseFloat(form.price.value),
      category: form.category.value,
      is_active: form.is_active?.checked ?? true
    };

    await API.put(`/v1/listings/${listingId}`, data);
    showFlash('Listing updated successfully!', 'success');
    setTimeout(() => window.location.href = `/listings/${listingId}`, 1000);

  } catch (error) {
    showFlash(error.data?.message || 'Failed to update listing', 'error');
  } finally {
    submitBtn.disabled = false;
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
    submitBtn.disabled = true;
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
    submitBtn.disabled = false;
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

  if (isAuth && user) {
    authNav.innerHTML = `
            <a href="/profile" class="btn btn-secondary btn-sm">${user.username}</a>
            <button onclick="handleLogout()" class="btn btn-secondary btn-sm">Logout</button>
        `;
  } else {
    authNav.innerHTML = `
            <a href="/login" class="btn btn-secondary btn-sm">Login</a>
            <a href="/register" class="btn btn-primary btn-sm">Sign Up</a>
        `;
  }
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
});
