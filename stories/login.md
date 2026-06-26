Title: Login - 有效凭据 (the-internet.herokuapp.com)

Base URL: https://the-internet.herokuapp.com

作为用户，我想使用有效凭据登录，以便访问安全区域。

验收条件：
- 导航到 `/login`
- 填写用户名 `tomsmith`
- 填写密码 `SuperSecretPassword!`
- 点击 Login 按钮
- 期望被重定向到 `/secure`
- 期望成功闪存消息可见，并包含文本：`You logged into a secure area!`
