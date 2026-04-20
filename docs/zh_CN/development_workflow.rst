.. _development-workflow-guide:

Fork 分支协作规范
=================

:link_to_translation:`en:[English]`

本文档定义 ESP-Brookesia fork 仓库的规范性分支工作流。

.. important::

   本页规则用于约束 fork 内部的长期分支协作方式。其目标是把“待上游合并的改动”“长期 fork 定制”和“日常开发分支”明确隔离。

分支职责
--------

fork 使用以下三条长期分支：

.. list-table:: 长期分支职责约定
   :header-rows: 1
   :widths: 25 30 45

   * - 分支
     - 角色
     - 内容边界
   * - ``master``
     - fork 的上游同步分支
     - 必须与 ``upstream/master`` 保持功能对齐。fork 专属改动不得直接进入该分支。
   * - ``integration/upstream-pending``
     - 承接“计划回馈官方上游、但尚未被上游合并”的聚合集成分支
     - 只能包含明确面向官方 upstream 的改动。fork 专属或产品专属改动不得进入该分支。
   * - ``integration/custom-base``
     - fork 的长期定制基线分支
     - 继承 ``integration/upstream-pending``，并仅追加稳定的 fork 自定义改动。该分支是内部日常开发的默认基线。

主题分支命名
------------

fork 使用以下主题分支命名族：

- ``upstream-pr/<topic>``：面向 upstream 的最小化主题分支
- ``dev/<topic>``：普通 fork 内部开发分支
- ``hotfix/<topic>``：紧急 fork 内部修复分支
- 现有 ``release/*`` 分支继续保持当前发布含义

建分支规则
----------

以下规则必须遵守：

- 不得直接在 ``master``、``integration/upstream-pending`` 或 ``integration/custom-base`` 上开发。
- ``upstream-pr/<topic>`` 默认从 ``master`` 拉出。
- 如果某个 upstream 主题分支依赖另一个尚未合并的 upstream 主题分支，应直接从其依赖分支拉出，而不是从 ``integration/upstream-pending`` 拉出。
- ``dev/<topic>`` 和 ``hotfix/<topic>`` 必须从 ``integration/custom-base`` 拉出。
- 不得使用 ``integration/upstream-pending`` 或 ``integration/custom-base`` 作为官方 upstream PR 的源分支。

更新规则
--------

刷新 ``integration/upstream-pending``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

应把 ``integration/upstream-pending`` 视为“可重建的聚合集成分支”，而不是自由提交的工作分支。

- 先用最新的 upstream 同步结果更新 ``master``。
- 从更新后的 ``master`` 重新创建或硬重置 ``integration/upstream-pending``。
- 仅按规范的依赖顺序，回放仍未被 upstream 合并的 ``upstream-pr/<topic>`` 分支。
- 不要通过反向回退已经被 upstream 合并的改动来维护该分支；应通过干净重建，让已合并主题自然消失。
- ``integration/upstream-pending`` 只能推送到 fork 远端（例如 ``origin``），不得推送到官方 upstream。

刷新 ``integration/custom-base``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

应把 ``integration/custom-base`` 视为“可重建或可重放”的 fork 长期基线。

- 以更新后的 ``integration/upstream-pending`` 为起点。
- 在其之上重新创建或 rebase ``integration/custom-base``。
- 仅回放 fork 专属的长期定制提交。
- 已经属于 ``integration/upstream-pending`` 的 upstream 向改动，不应继续在 ``integration/custom-base`` 中单独维护。

PR 规则
-------

- 面向官方 upstream 的 PR 必须来自最小化的 ``upstream-pr/<topic>`` 分支。
- fork 内部 PR 默认应以 ``integration/custom-base`` 为目标分支。
- 只有明确用于维护聚合集成层的 PR，才可以以 ``integration/upstream-pending`` 为目标分支。
- 两条 integration 分支是集成基线，不是功能开发分支。

执行控制
--------

仓库管理员应在仓库托管平台上补充以下保护设置：

- 保护 ``master``
- 保护 ``integration/upstream-pending``
- 保护 ``integration/custom-base``
- 除批准的分支维护操作外，禁止直接推送

如果暂时无法立即配置分支保护，也必须至少把本页规则作为团队执行约定严格遵守。

示例流程
--------

新增一个上游待合并主题
^^^^^^^^^^^^^^^^^^^^^^

1. 从 ``master`` 拉出 ``upstream-pr/<topic>``。
2. 在该分支上完成并评审最小化的 upstream 改动。
3. 通过回放该主题分支以及其他仍未合并的 upstream 主题，刷新 ``integration/upstream-pending``。
4. 再基于更新后的聚合集成层刷新 ``integration/custom-base``。

当 upstream 已合并其中一个待集成 PR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. 先把 ``master`` 更新到最新 upstream 同步状态。
2. 从 ``master`` 重建 ``integration/upstream-pending``，只回放仍未合并的 upstream 主题分支。
3. 再基于新的聚合集成层重建或 rebase ``integration/custom-base``。

新增一个 fork 专属长期定制
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. 从 ``integration/custom-base`` 拉出 ``dev/<topic>``。
2. 评审完成后，把结果合回 ``integration/custom-base``。
3. 除非该改动明确要回馈 upstream，否则不要放进 ``integration/upstream-pending``。

开始一个普通内部开发任务
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. 默认以 ``integration/custom-base`` 作为开发起点。
2. 按需创建 ``dev/<topic>`` 或 ``hotfix/<topic>``。
3. 不要把内部开发直接放到 ``master`` 或 ``integration/upstream-pending``。
