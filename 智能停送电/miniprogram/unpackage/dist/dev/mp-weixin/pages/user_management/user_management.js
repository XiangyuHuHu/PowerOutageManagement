"use strict";
const common_vendor = require("../../common/vendor.js");
const _sfc_main = {
  data() {
    return {
      users: [],
      loading: false,
      stats: {
        total: 0,
        admin: 0,
        dispatcher: 0,
        electrician: 0
      },
      showEditDialog: false,
      editForm: {
        id: null,
        username: "",
        realname: "",
        role: "",
        password: ""
      },
      roleOptions: ["管理员", "调度员", "电工", "普通用户"],
      editRoleIndex: 0,
      saving: false
    };
  },
  onLoad() {
    common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:132", "用户管理页面加载开始");
    setTimeout(() => {
      this.checkPermission();
    }, 200);
    setTimeout(() => {
      this.fetchUsers();
    }, 1e3);
  },
  onShow() {
    common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:144", "用户管理页面显示");
  },
  methods: {
    checkPermission() {
      const userRole = common_vendor.index.getStorageSync("user_role");
      common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:150", "检查权限，用户角色:", userRole);
      if (userRole !== "admin") {
        common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:152", "权限不足，用户角色不是admin");
        common_vendor.index.showToast({
          title: "只有管理员可以访问用户管理页面",
          icon: "none",
          duration: 2e3
        });
        setTimeout(() => {
          common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:160", "执行navigateBack");
          common_vendor.index.navigateBack();
        }, 500);
      } else {
        common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:164", "权限检查通过");
      }
    },
    goBack() {
      common_vendor.index.navigateBack();
    },
    getRoleText(role) {
      const roleMap = {
        "admin": "管理员",
        "dispatcher": "调度员",
        "electrician": "电工",
        "user": "普通用户"
      };
      return roleMap[role] || role;
    },
    async fetchUsers() {
      common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:183", "开始获取用户列表");
      this.loading = true;
      try {
        const response = await common_vendor.index.request({
          url: "http://localhost:5050/api/mp/users",
          method: "GET",
          header: {
            "Content-Type": "application/json"
          },
          timeout: 15e3
        });
        common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:195", "用户列表响应:", response);
        if (response.statusCode === 200) {
          this.users = response.data;
          this.updateStats();
          common_vendor.index.__f__("log", "at pages/user_management/user_management.vue:200", "用户列表获取成功，共", this.users.length, "个用户");
        } else {
          common_vendor.index.__f__("error", "at pages/user_management/user_management.vue:202", "获取用户列表失败，状态码:", response.statusCode);
          common_vendor.index.showToast({
            title: "获取用户列表失败",
            icon: "none"
          });
        }
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/user_management/user_management.vue:209", "获取用户列表失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.loading = false;
      }
    },
    updateStats() {
      this.stats.total = this.users.length;
      this.stats.admin = this.users.filter((u) => u.role === "admin").length;
      this.stats.dispatcher = this.users.filter((u) => u.role === "dispatcher").length;
      this.stats.electrician = this.users.filter((u) => u.role === "electrician").length;
    },
    editUser(user) {
      this.editForm = {
        id: user.id,
        username: user.username,
        realname: user.realname,
        role: user.role,
        password: ""
      };
      const roleIndexMap = {
        "admin": 0,
        "dispatcher": 1,
        "electrician": 2,
        "user": 3
      };
      this.editRoleIndex = roleIndexMap[user.role] || 0;
      this.showEditDialog = true;
    },
    onEditRoleChange(e) {
      this.editRoleIndex = e.detail.value;
      const roleMap = ["admin", "dispatcher", "electrician", "user"];
      this.editForm.role = roleMap[this.editRoleIndex];
    },
    closeEditDialog() {
      this.showEditDialog = false;
      this.editForm = {
        id: null,
        username: "",
        realname: "",
        role: "",
        password: ""
      };
    },
    async saveUser() {
      if (!this.editForm.username || !this.editForm.realname) {
        common_vendor.index.showToast({
          title: "请填写完整信息",
          icon: "none"
        });
        return;
      }
      this.saving = true;
      try {
        common_vendor.index.showToast({
          title: "编辑功能开发中",
          icon: "none"
        });
        this.closeEditDialog();
      } catch (err) {
        common_vendor.index.__f__("error", "at pages/user_management/user_management.vue:281", "保存用户失败:", err);
        common_vendor.index.showToast({
          title: "网络错误",
          icon: "none"
        });
      } finally {
        this.saving = false;
      }
    },
    async deleteUser(userId) {
      common_vendor.index.showModal({
        title: "确认删除",
        content: "确定要删除这个用户吗？",
        success: async (res) => {
          if (res.confirm) {
            common_vendor.index.showToast({
              title: "删除功能开发中",
              icon: "none"
            });
          }
        }
      });
    }
  }
};
function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return common_vendor.e({
    a: common_vendor.o((...args) => $options.goBack && $options.goBack(...args)),
    b: common_vendor.t($data.stats.total),
    c: common_vendor.t($data.stats.admin),
    d: common_vendor.t($data.stats.dispatcher),
    e: common_vendor.t($data.stats.electrician),
    f: common_vendor.t($data.loading ? "刷新中..." : "刷新"),
    g: common_vendor.o((...args) => $options.fetchUsers && $options.fetchUsers(...args)),
    h: $data.loading,
    i: $data.loading
  }, $data.loading ? {} : $data.users.length === 0 ? {} : {
    k: common_vendor.f($data.users, (user, k0, i0) => {
      return common_vendor.e({
        a: common_vendor.t(user.realname),
        b: common_vendor.t(user.username),
        c: common_vendor.t($options.getRoleText(user.role)),
        d: common_vendor.o(($event) => $options.editUser(user), user.id),
        e: user.role !== "admin"
      }, user.role !== "admin" ? {
        f: common_vendor.o(($event) => $options.deleteUser(user.id), user.id)
      } : {}, {
        g: user.id
      });
    })
  }, {
    j: $data.users.length === 0,
    l: $data.showEditDialog
  }, $data.showEditDialog ? {
    m: common_vendor.o((...args) => $options.closeEditDialog && $options.closeEditDialog(...args)),
    n: $data.editForm.username,
    o: common_vendor.o(($event) => $data.editForm.username = $event.detail.value),
    p: $data.editForm.realname,
    q: common_vendor.o(($event) => $data.editForm.realname = $event.detail.value),
    r: common_vendor.t($data.roleOptions[$data.editRoleIndex]),
    s: $data.editRoleIndex,
    t: $data.roleOptions,
    v: common_vendor.o((...args) => $options.onEditRoleChange && $options.onEditRoleChange(...args)),
    w: $data.editForm.password,
    x: common_vendor.o(($event) => $data.editForm.password = $event.detail.value),
    y: common_vendor.o((...args) => $options.closeEditDialog && $options.closeEditDialog(...args)),
    z: common_vendor.t($data.saving ? "保存中..." : "保存"),
    A: common_vendor.o((...args) => $options.saveUser && $options.saveUser(...args)),
    B: $data.saving,
    C: common_vendor.o(() => {
    }),
    D: common_vendor.o((...args) => $options.closeEditDialog && $options.closeEditDialog(...args))
  } : {});
}
const MiniProgramPage = /* @__PURE__ */ common_vendor._export_sfc(_sfc_main, [["render", _sfc_render]]);
wx.createPage(MiniProgramPage);
//# sourceMappingURL=../../../.sourcemap/mp-weixin/pages/user_management/user_management.js.map
