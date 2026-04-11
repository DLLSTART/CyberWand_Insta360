// OpenClaw Browser Relay - 修复版后台脚本
// 移除 Native Messaging 依赖，改用本地存储 + 消息传递

let isConnected = false;
let activeTabId = null;

// 扩展安装时初始化
chrome.runtime.onInstalled.addListener(() => {
  console.log('OpenClaw Browser Relay installed');
  updateBadge(false);
});

// 监听扩展图标点击
chrome.action.onClicked.addListener(() => {
  activateCurrentTab();
});

// 监听来自 popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);
  
  switch (request.action) {
    case 'activate':
      activateCurrentTab();
      sendResponse({ success: true, message: '已激活' });
      break;
    
    case 'deactivate':
      deactivateTab();
      sendResponse({ success: true, message: '已停用' });
      break;
    
    case 'getStatus':
      sendResponse({ 
        success: true, 
        isConnected: isConnected,
        activeTabId: activeTabId 
      });
      break;
    
    case 'getActiveTab':
      if (activeTabId) {
        chrome.tabs.get(activeTabId, (tab) => {
          sendResponse({ 
            success: true, 
            tab: {
              id: tab.id,
              url: tab.url,
              title: tab.title
            }
          });
        });
        return true; // 保持消息通道开放
      } else {
        sendResponse({ success: false, message: '未激活任何标签' });
      }
      break;
    
    default:
      sendResponse({ success: false, message: '未知操作' });
  }
  
  return true;
});

// 激活当前标签
function activateCurrentTab() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length > 0) {
      const tab = tabs[0];
      activeTabId = tab.id;
      isConnected = true;
      
      // 更新徽章状态
      updateBadge(true);
      
      // 发送激活通知
      chrome.tabs.sendMessage(tab.id, {
        action: 'activated',
        tabInfo: {
          url: tab.url,
          title: tab.title
        }
      }).catch(err => {
        console.log('发送消息失败（可能是非 HTTP 页面）:', err);
      });
      
      console.log('已激活标签:', tab.url);
    } else {
      console.error('未找到活动标签');
    }
  });
}

// 停用标签
function deactivateTab() {
  if (activeTabId) {
    // 通知内容脚本
    chrome.tabs.sendMessage(activeTabId, {
      action: 'deactivated'
    }).catch(err => console.log('发送消息失败:', err));
  }
  
  activeTabId = null;
  isConnected = false;
  updateBadge(false);
  console.log('已停用标签');
}

// 更新徽章显示
function updateBadge(activated) {
  if (activated) {
    chrome.action.setBadgeText({ text: 'ON' });
    chrome.action.setBadgeBackgroundColor({ color: '#07c160' }); // 绿色
  } else {
    chrome.action.setBadgeText({ text: '' });
    chrome.action.setBadgeBackgroundColor({ color: '#AAAAAA' }); // 灰色
  }
}

// 标签页关闭时清理
chrome.tabs.onRemoved.addListener((tabId) => {
  if (tabId === activeTabId) {
    deactivateTab();
  }
});

// 标签页切换时更新
chrome.tabs.onActivated.addListener((activeInfo) => {
  // 可选：自动切换到新标签
  // activateTabById(activeInfo.tabId);
});
