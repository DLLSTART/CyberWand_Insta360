// OpenClaw Browser Relay - 修复版弹出页面脚本

const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const activateBtn = document.getElementById('activateBtn');
const deactivateBtn = document.getElementById('deactivateBtn');
const tabInfo = document.getElementById('tabInfo');
const tabUrl = document.getElementById('tabUrl');
const tabTitle = document.getElementById('tabTitle');

// 更新状态显示
function updateStatus(connected, tabData = null) {
  if (connected) {
    statusIndicator.className = 'indicator active';
    statusText.textContent = '已激活';
    activateBtn.textContent = '✅ 已激活';
    activateBtn.disabled = true;
    activateBtn.style.opacity = '0.6';
    
    if (tabData) {
      tabInfo.style.display = 'block';
      tabUrl.textContent = tabData.url || '未知';
      tabTitle.textContent = tabData.title || '未知标题';
    }
  } else {
    statusIndicator.className = 'indicator';
    statusText.textContent = '未激活';
    activateBtn.textContent = '✨ 激活当前标签';
    activateBtn.disabled = false;
    activateBtn.style.opacity = '1';
    tabInfo.style.display = 'none';
  }
}

// 获取当前状态
function getStatus() {
  chrome.runtime.sendMessage({ action: 'getStatus' }, (response) => {
    if (response && response.success) {
      if (response.isConnected && response.activeTabId) {
        // 获取激活的标签信息
        chrome.runtime.sendMessage({ action: 'getActiveTab' }, (tabResponse) => {
          if (tabResponse && tabResponse.success) {
            updateStatus(true, tabResponse.tab);
          } else {
            updateStatus(true, null);
          }
        });
      } else {
        updateStatus(false, null);
      }
    } else {
      updateStatus(false, null);
    }
  });
}

// 激活当前标签
activateBtn.addEventListener('click', () => {
  activateBtn.textContent = '⏳ 激活中...';
  activateBtn.disabled = true;
  
  chrome.runtime.sendMessage({ action: 'activate' }, (response) => {
    if (response && response.success) {
      // 获取标签信息
      chrome.runtime.sendMessage({ action: 'getActiveTab' }, (tabResponse) => {
        if (tabResponse && tabResponse.success) {
          updateStatus(true, tabResponse.tab);
        } else {
          updateStatus(true, null);
        }
      });
    } else {
      alert('激活失败：' + (response?.message || '请重试'));
      getStatus();
    }
  });
});

// 停用标签
deactivateBtn.addEventListener('click', () => {
  chrome.runtime.sendMessage({ action: 'deactivate' }, (response) => {
    if (response && response.success) {
      updateStatus(false, null);
    } else {
      alert('停用失败');
    }
  });
});

// 页面加载时获取状态
getStatus();
