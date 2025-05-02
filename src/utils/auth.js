// 认证工具类

// 检查用户是否已登录
export const isAuthenticated = () => {
  return !!localStorage.getItem("authToken");
};

// 获取当前用户信息
export const getCurrentUser = () => {
  const userStr = localStorage.getItem("user");
  return userStr ? JSON.parse(userStr) : null;
};

// 获取认证令牌
export const getToken = () => {
  return localStorage.getItem("authToken");
};

// 设置用户登录信息
export const setAuth = (token, user) => {
  localStorage.setItem("authToken", token);
  localStorage.setItem("user", JSON.stringify(user));
};

// 清除用户登录信息
export const clearAuth = () => {
  localStorage.removeItem("authToken");
  localStorage.removeItem("user");
};

// 为API请求添加认证头
export const getAuthHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Token ${token}` } : {};
};
