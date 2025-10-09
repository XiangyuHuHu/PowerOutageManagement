"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      tasks: [],
      stats: {
        total: 0,
        pending: 0,
        inProgress: 0,
        completed: 0
      },
      loading: false,
      showDialog: false,
      isEdit: false,
      taskForm: {
        id: null,
        title: "",
        description: "",
        deviceId: "",
        assignee: "",
        status: "pending",
        deadline: ""
      },
      statusOptions: ["待处理", "进行中", "已完成", "已取消"],
      statusIndex: 0,
      saving: false
    };
  },
  onLoad() {
    this.fetchTasks();
  },
  methods: {
    getStatusText(status) {
      const statusMap = {
        "pending": "待处理",
        "in_progress": "进行中",
        "completed": "已完成",
        "cancelled": "已取消"
      };
      return statusMap[status] || status;
    },
    formatDateTime(timestamp) {
      if (!timestamp)
        return "";
      let dateStr = timestamp;
      if (typeof timestamp === "string") {
        dateStr = timestamp.replace(/-/g, "/");
      }
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) {
        return timestamp;
      }
      return date.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      });
    },
    async fetchTasks() {
      this.loading = true;
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/applications",
          method: "GET",
          header: {
            "Content-Type": "application/json"
          },
          timeout: 15e3
        });
        if (response.statusCode === 200) {
          this.tasks = response.data.map((app) => ({
            id: app.id,
            title: `${app.deviceId} - ${app.reason}`,
            description: `申请人: ${app.applicant_name || app.applicant}, 原因: ${app.reason}`,
            deviceId: app.deviceId,
            assignee: app.applicant_name || app.applicant,
            status: this.mapApplicationStatusToTaskStatus(app.status),
            created_at: app.created_at,
            deadline: app.power_off_time,
            originalApplication: app
            // 保存原始申请数据
          }));
          this.updateStats();
          common_vendor.index.__f__("log", "at pages/repair/repair.vue:265", "检修任务获取成功，共", this.tasks.length, "个任务");
        } else {
          common_vendor.index.__f__("error", "at pages/repair/repair.vue:267", "获取检修任务失败，状态码:", response.statusCode);
          common_vendor.index.showToast({
            title: "获取检修任务失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/repair/repair.vue:274", "获取检修任务失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    },
    mapApplicationStatusToTaskStatus(appStatus) {
      const statusMap = {
        "pending": "pending",
        "approved": "in_progress",
        "verified": "in_progress",
        "repairing": "in_progress",
        "repair_completed": "completed",
        "completed": "completed",
        "rejected": "cancelled",
        "power_on_applied": "completed",
        "power_on_rejected": "cancelled"
      };
      return statusMap[appStatus] || "pending";
    },
    updateStats() {
      this.stats.total = this.tasks.length;
      this.stats.pending = this.tasks.filter((t) => t.status === "pending").length;
      this.stats.inProgress = this.tasks.filter((t) => t.status === "in_progress").length;
      this.stats.completed = this.tasks.filter((t) => t.status === "completed").length;
      common_vendor.index.__f__("log", "at pages/repair/repair.vue:304", "检修统计更新:", this.stats);
    },
    showAddDialog() {
      this.isEdit = false;
      this.taskForm = {
        id: null,
        title: "",
        description: "",
        deviceId: "",
        assignee: "",
        status: "pending",
        deadline: ""
      };
      this.statusIndex = 0;
      this.showDialog = true;
    },
    editTask(task) {
      this.isEdit = true;
      this.taskForm = { ...task };
      const statusIndexMap = {
        "pending": 0,
        "in_progress": 1,
        "completed": 2,
        "cancelled": 3
      };
      this.statusIndex = statusIndexMap[task.status] || 0;
      this.showDialog = true;
      common_vendor.index.__f__("log", "at pages/repair/repair.vue:336", "编辑任务:", task);
    },
    onStatusChange(e) {
      this.statusIndex = e.detail.value;
      const statusMap = ["pending", "in_progress", "completed", "cancelled"];
      this.taskForm.status = statusMap[this.statusIndex];
    },
    onDateChange(e) {
      this.taskForm.deadline = e.detail.value;
    },
    closeDialog() {
      this.showDialog = false;
      this.taskForm = {
        id: null,
        title: "",
        description: "",
        deviceId: "",
        assignee: "",
        status: "pending",
        deadline: ""
      };
    },
    async saveTask() {
      if (!this.taskForm.title.trim()) {
        common_vendor.index.showToast({
          title: "请输入任务标题",
          icon: "none"
        });
        return;
      }
      if (!this.taskForm.description.trim()) {
        common_vendor.index.showToast({
          title: "请输入任务描述",
          icon: "none"
        });
        return;
      }
      if (!this.taskForm.deviceId.trim()) {
        common_vendor.index.showToast({
          title: "请输入设备ID",
          icon: "none"
        });
        return;
      }
      if (!this.taskForm.assignee.trim()) {
        common_vendor.index.showToast({
          title: "请输入负责人",
          icon: "none"
        });
        return;
      }
      this.saving = true;
      try {
        if (this.isEdit && this.taskForm.originalApplication) {
          const newStatus = this.mapTaskStatusToApplicationStatus(this.taskForm.status);
          let apiUrl = "";
          let apiData = { id: this.taskForm.originalApplication.id };
          if (newStatus === "approved") {
            apiUrl = "http://localhost:5050/api/mp/approve-application";
          } else if (newStatus === "rejected") {
            apiUrl = "http://localhost:5050/api/mp/reject-application";
          } else if (newStatus === "completed") {
            apiUrl = "http://localhost:5050/api/mp/approve-power-on";
          }
          if (apiUrl) {
            const response = await common_vendor.index.request({
              url: apiUrl,
              method: "POST",
              header: {
                "Content-Type": "application/json"
              },
              data: apiData,
              timeout: 1e4
            });
            if (response.statusCode === 200) {
              common_vendor.index.showToast({
                title: "状态更新成功",
                icon: "success"
              });
              this.closeDialog();
              this.fetchTasks();
            } else {
              common_vendor.index.showToast({
                title: "状态更新失败",
                icon: "none"
              });
            }
          } else {
            common_vendor.index.showToast({
              title: "不支持的状态更新",
              icon: "none"
            });
          }
        } else {
          common_vendor.index.showToast({
            title: "新建功能开发中",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/repair/repair.vue:451", "保存失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.saving = false;
      }
    },
    mapTaskStatusToApplicationStatus(taskStatus) {
      const statusMap = {
        "pending": "pending",
        "in_progress": "approved",
        "completed": "completed",
        "cancelled": "rejected"
      };
      return statusMap[taskStatus] || "pending";
    },
    async deleteTask(taskId) {
      common_vendor.index.showModal({
        title: "确认删除",
        content: "确定要删除这个任务吗？",
        success: (res) => {
          if (res.confirm) {
            this.tasks = this.tasks.filter((t) => t.id !== taskId);
            this.updateStats();
            common_vendor.index.showToast({
              title: "任务删除成功",
              icon: "success"
            });
          }
        }
      });
    },
    viewTask(task) {
      common_vendor.index.showModal({
        title: task.title,
        content: `设备ID: ${task.deviceId}
负责人: ${task.assignee}
状态: ${this.getStatusText(task.status)}
描述: ${task.description}`,
        showCancel: false
      });
    },
    goBack() {
      common_vendor.index.navigateBack();
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: common_vendor.t($data.stats.total),
    c: common_vendor.t($data.stats.pending),
    d: common_vendor.t($data.stats.inProgress),
    e: common_vendor.t($data.stats.completed),
    f: common_vendor.o((...args) => $options.showAddDialog && $options.showAddDialog(...args)),
    g: $data.loading
  }, $data.loading ? {} : $data.tasks.length === 0 ? {} : {
    i: common_vendor.f($data.tasks, (task, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(task.title),
        b: common_vendor.t($options.getStatusText(task.status)),
        c: common_vendor.n("status-" + task.status),
        d: common_vendor.t(task.description),
        e: common_vendor.t(task.deviceId),
        f: common_vendor.t(task.assignee),
        g: common_vendor.t($options.formatDateTime(task.created_at)),
        h: task.deadline
      }, task.deadline ? {
        i: common_vendor.t($options.formatDateTime(task.deadline))
      } : {}, {
        j: common_vendor.o(($event) => $options.editTask(task), task.id),
        k: common_vendor.o(($event) => $options.deleteTask(task.id), task.id),
        l: task.id,
        m: common_vendor.o(($event) => $options.viewTask(task), task.id)
      });
    })
  }, {
    h: $data.tasks.length === 0,
    j: $data.showDialog
  }, $data.showDialog ? {
    k: common_vendor.t($data.isEdit ? "编辑任务" : "新建任务"),
    l: common_vendor.o((...args) => $options.closeDialog && $options.closeDialog(...args)),
    m: $data.taskForm.title,
    n: common_vendor.o(($event) => $data.taskForm.title = $event.detail.value),
    o: $data.taskForm.description,
    p: common_vendor.o(($event) => $data.taskForm.description = $event.detail.value),
    q: $data.taskForm.deviceId,
    r: common_vendor.o(($event) => $data.taskForm.deviceId = $event.detail.value),
    s: $data.taskForm.assignee,
    t: common_vendor.o(($event) => $data.taskForm.assignee = $event.detail.value),
    v: common_vendor.t($data.statusOptions[$data.statusIndex]),
    w: $data.statusIndex,
    x: $data.statusOptions,
    y: common_vendor.o((...args) => $options.onStatusChange && $options.onStatusChange(...args)),
    z: common_vendor.t($data.taskForm.deadline || "请选择截止时间"),
    A: $data.taskForm.deadline,
    B: common_vendor.o((...args) => $options.onDateChange && $options.onDateChange(...args)),
    C: common_vendor.t($data.saving ? "保存中..." : "保存"),
    D: common_vendor.o((...args) => $options.saveTask && $options.saveTask(...args)),
    E: $data.saving,
    F: common_vendor.o((...args) => $options.closeDialog && $options.closeDialog(...args)),
    G: common_vendor.o(() => {
    }),
    H: common_vendor.o((...args) => $options.closeDialog && $options.closeDialog(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render], ["__scopeId", "data-v-ad4deb87"]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/repair/repair.js.map
