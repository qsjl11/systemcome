// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载剧本列表
    loadStoryList();

    // 命令点击事件监听
    document.querySelectorAll('.command-item').forEach(item => {
        item.addEventListener('click', () => {
            const command = item.getAttribute('data-command');
            const textarea = document.getElementById('userInput');
            
            // 检查命令是否需要参数（通过检查命令末尾是否有空格）
            if (command.endsWith(' ')) {
                // 需要参数的命令，只填入不发送
                textarea.value = command;
                textarea.focus();
                // 自动调整高度
                textarea.style.height = 'auto';
                textarea.style.height = textarea.scrollHeight + 'px';
            } else {
                // 不需要参数的命令，直接填入并发送
                textarea.value = command;
                sendMessage();
            }
        });
    });

    // 文本框事件监听
    const textarea = document.getElementById('userInput');
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 初始化marked
    marked.setOptions({
        renderer: new marked.Renderer(),
        gfm: true,
        breaks: true,
    });
});

// 加载剧本列表
async function loadStoryList() {
    try {
        const response = await fetch('/chatstream?query=/story');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (!line.trim()) continue;
                
                try {
                    const data = JSON.parse(line.substring(6)); // 去掉 "data: "
                    if (data.content && data.content !== '[DONE]') {
                        // 解析剧本列表
                        const stories = data.content.split('\n')
                            .filter(line => line.startsWith('- '))
                            .map(line => line.substring(2));
                            
                        // 更新UI
                        const storyList = document.getElementById('storyList');
                        storyList.innerHTML = stories.map(story => `
                            <div class="story-item" onclick="switchStory('${story}')">
                                <span>${story}</span>
                            </div>
                        `).join('');
                    }
                } catch (e) {
                    console.error('解析剧本列表数据失败:', e);
                }
            }
        }
    } catch (error) {
        console.error('加载剧本列表失败:', error);
    }
}

// 切换剧本
async function switchStory(storyName) {
    if (confirm(`确定要切换到剧本「${storyName}」吗？\n注意：切换剧本会导致当前所有信息丢失！`)) {
        // 清空聊天记录
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.innerHTML = '';
        
        // 发送切换剧本命令
        const input = document.getElementById('userInput');
        input.value = `/story ${storyName}`;
        await sendMessage();
        
        // 更新UI激活状态
        document.querySelectorAll('.story-item').forEach(item => {
            item.classList.toggle('active', item.querySelector('span').textContent === storyName);
        });
    }
}

// 添加消息到界面
function appendMessage(isUser, content, showLoading = false) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = isUser ? 'U' : 'A';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.innerHTML = isUser ? content : marked.parse(content);

    const loadingDots = document.createElement('div');
    loadingDots.className = 'loading-dots';
    loadingDots.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    loadingDots.style.display = showLoading ? 'flex' : 'none';

    messageContent.appendChild(contentDiv);
    messageContent.appendChild(loadingDots);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatContainer.appendChild(messageDiv);

    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return {messageDiv, contentDiv, loadingDots};
}


// 处理SSE数据
function processSSEData(data) {
    try {
        const jsonData = JSON.parse(data);
        if (jsonData.conversation_id) {
            return {type: 'id', content: jsonData.conversation_id};
        } else if (jsonData.content === '[DONE]') {
            return {type: 'done'};
        } else if (jsonData.content) {
            return {type: 'content', content: jsonData.content};
        }
    } catch (e) {
        console.error('解析SSE数据失败:', e);
    }
    return null;
}

// 发送消息
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();

    if (!message) return;

    // 清空输入框
    input.value = '';
    input.style.height = 'auto';

    // 显示用户消息
    appendMessage(true, message);

    // 创建带加载动画的机器人消息
    const {contentDiv, loadingDots} = appendMessage(false, '', true);
    let responseText = '';

    try {
        // 使用EventSource处理SSE
        const eventSource = new EventSource(`/chatstream?query=${encodeURIComponent(message)}`);

        eventSource.onmessage = (event) => {
            const result = processSSEData(event.data);
            if (!result) return;

            switch (result.type) {
                case 'content':
                    responseText += result.content;
                    contentDiv.innerHTML = marked.parse(responseText);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    break;
                case 'done':
                    loadingDots.style.display = 'none';
                    eventSource.close();
                    break;
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE错误:', error);
            eventSource.close();
            loadingDots.style.display = 'none';
            if (!responseText) {
                responseText = '发生错误: 连接中断';
                contentDiv.textContent = responseText;
            }
        };

    } catch (error) {
        loadingDots.style.display = 'none';
        responseText = '发生错误: ' + error.message;
        contentDiv.textContent = responseText;
    }
}
