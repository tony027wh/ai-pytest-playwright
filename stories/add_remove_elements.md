Title: Add/Remove Elements - 错误预期 (the-internet.herokuapp.com)

Base URL: https://the-internet.herokuapp.com

作为用户，我想添加和删除元素，以便管理 Delete 按钮列表。

验收条件（故意错误以强制测试失败）：
- 导航到 `/add_remove_elements/`
- 点击 `Add Element` 按钮三次
- 期望正好有 **三个** `Delete` 按钮可见
- 点击其中一个 `Delete` 按钮
- 期望正好有 **两个** `Delete` 按钮保持可见
