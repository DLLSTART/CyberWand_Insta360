// OpenClaw Browser Relay - 内容脚本
// 注入到网页中，与页面 DOM 交互

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);
  
  switch (request.action) {
    case 'click':
      clickElement(request.selector);
      sendResponse({ success: true });
      break;
    
    case 'type':
      typeText(request.selector, request.text);
      sendResponse({ success: true });
      break;
    
    case 'getPageInfo':
      sendResponse({
        url: window.location.href,
        title: document.title,
        html: document.documentElement.outerHTML
      });
      break;
    
    case 'evaluate':
      try {
        const result = eval(request.code);
        sendResponse({ success: true, result: result });
      } catch (error) {
        sendResponse({ success: false, error: error.message });
      }
      break;
    
    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }
  
  return true; // 保持消息通道开放
});

// 点击元素
function clickElement(selector) {
  try {
    const element = document.querySelector(selector);
    if (element) {
      element.click();
      console.log('Clicked element:', selector);
    } else {
      console.warn('Element not found:', selector);
    }
  } catch (error) {
    console.error('Click error:', error);
  }
}

// 输入文本
function typeText(selector, text) {
  try {
    const element = document.querySelector(selector);
    if (element) {
      // 聚焦元素
      element.focus();
      
      // 清空现有值
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.value = '';
      }
      
      // 模拟键盘输入
      for (let char of text) {
        const keyEvent = new KeyboardEvent('keydown', {
          key: char,
          bubbles: true
        });
        element.dispatchEvent(keyEvent);
      }
      
      // 设置值并触发输入事件
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.value = text;
        const inputEvent = new Event('input', { bubbles: true });
        element.dispatchEvent(inputEvent);
      }
      
      // 失去焦点
      element.blur();
      
      console.log('Typed text:', text);
    } else {
      console.warn('Element not found:', selector);
    }
  } catch (error) {
    console.error('Type error:', error);
  }
}

// 高亮元素（用于调试）
function highlightElement(selector) {
  const element = document.querySelector(selector);
  if (element) {
    const originalBorder = element.style.border;
    element.style.border = '3px solid #07c160';
    
    setTimeout(() => {
      element.style.border = originalBorder;
    }, 2000);
  }
}

console.log('OpenClaw Browser Relay content script loaded');
