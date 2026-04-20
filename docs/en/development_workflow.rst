.. _development-workflow-guide:

Fork Development Workflow
=========================

:link_to_translation:`zh_CN:[中文]`

This page defines the normative branch workflow for maintaining the ESP-Brookesia fork.

.. important::

   The rules on this page are mandatory for branch usage inside the fork. They are written to keep upstream-bound work, long-lived fork customizations, and day-to-day feature development separated.

Branch Roles
------------

The fork uses three permanent long-lived branches:

.. list-table:: Permanent branch contract
   :header-rows: 1
   :widths: 25 30 45

   * - Branch
     - Role
     - Required content boundary
   * - ``master``
     - Upstream-sync branch for the fork mirror
     - Must stay functionally aligned with ``upstream/master``. Fork-only changes must not land here.
   * - ``integration/upstream-pending``
     - Aggregate branch for upstream-bound work that is not merged upstream yet
     - May contain only changes that are intended to be merged into official upstream. Fork-only or product-only changes must not land here.
   * - ``integration/custom-base``
     - Long-lived fork baseline
     - Inherits ``integration/upstream-pending`` and adds only stable fork-specific customizations. This is the default base for internal development.

Topic Branch Naming
-------------------

The fork uses the following topic branch families:

- ``upstream-pr/<topic>``: minimal upstream-facing topic branches
- ``dev/<topic>``: normal fork-only development branches
- ``hotfix/<topic>``: urgent fork-only fixes
- Existing ``release/*`` branches keep their current release meaning

Branch Creation Rules
---------------------

The following rules are mandatory:

- Do not develop directly on ``master``, ``integration/upstream-pending``, or ``integration/custom-base``.
- Create ``upstream-pr/<topic>`` branches from ``master`` by default.
- If an upstream-facing topic branch depends on another unmerged upstream-facing topic branch, branch from that dependent topic branch directly instead of from ``integration/upstream-pending``.
- Create ``dev/<topic>`` and ``hotfix/<topic>`` branches from ``integration/custom-base``.
- Do not open official upstream pull requests from ``integration/upstream-pending`` or ``integration/custom-base``.

Update Rules
------------

Refreshing ``integration/upstream-pending``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Treat ``integration/upstream-pending`` as a rebuilt aggregate branch, not as a freeform working branch.

- Update ``master`` from the latest fork copy of ``upstream/master`` first.
- Recreate or hard-reset ``integration/upstream-pending`` from the updated ``master``.
- Replay only the remaining unmerged ``upstream-pr/<topic>`` branches in canonical dependency order.
- Do not revert already-merged upstream work out of the aggregate branch. Rebuild the branch cleanly so merged topics naturally disappear.
- Push ``integration/upstream-pending`` only to the fork remote (for example ``origin``), never to official upstream.

Refreshing ``integration/custom-base``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Treat ``integration/custom-base`` as a rebuilt or rebased fork baseline.

- Start from the updated ``integration/upstream-pending`` branch.
- Recreate or rebase ``integration/custom-base`` on top of it.
- Replay only fork-specific long-lived custom commits.
- Do not keep upstream-bound commits here once they already belong to ``integration/upstream-pending``.

PR Policy
---------

- Official upstream pull requests must come from minimal ``upstream-pr/<topic>`` branches.
- Fork-internal pull requests should target ``integration/custom-base`` by default.
- Only maintenance pull requests that intentionally refresh the aggregate branch may target ``integration/upstream-pending``.
- Integration branches are staging baselines, not feature branches.

Operational Controls
--------------------

Repository admins should enforce these usage rules with hosting settings outside the repository:

- protect ``master``
- protect ``integration/upstream-pending``
- protect ``integration/custom-base``
- disallow direct pushes except for approved branch-maintenance operations

If branch protection cannot be enforced immediately, the team must still follow the rules on this page as the minimum operating contract.

Example Flows
-------------

Adding a new upstream-bound PR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Branch ``upstream-pr/<topic>`` from ``master``.
2. Implement and review the minimal upstream-facing change there.
3. Refresh ``integration/upstream-pending`` by replaying that topic branch together with the other still-unmerged upstream topics.
4. Refresh ``integration/custom-base`` on top of the updated aggregate branch.

Upstream merges one carried PR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Update ``master`` from the latest upstream-synced state.
2. Rebuild ``integration/upstream-pending`` from ``master`` plus only the still-unmerged upstream topic branches.
3. Rebuild or rebase ``integration/custom-base`` on the refreshed aggregate branch.

Adding a fork-only customization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Branch ``dev/<topic>`` from ``integration/custom-base``.
2. Merge the reviewed result back into ``integration/custom-base``.
3. Do not place the change into ``integration/upstream-pending`` unless it is intentionally being prepared for official upstream.

Starting normal internal development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Use ``integration/custom-base`` as the default starting point.
2. Create ``dev/<topic>`` or ``hotfix/<topic>`` as appropriate.
3. Keep internal work out of ``master`` and ``integration/upstream-pending``.
