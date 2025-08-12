<template>
	<view class="register-container">
		<view class="register-header">
			<view class="logo">
				<text class="logo-text">智能停送电系统</text>
			</view>
			<text class="subtitle">用户注册</text>
		</view>
		
		<view class="register-form">
			<view class="form-group">
				<text class="label">用户名</text>
				<input 
					class="input" 
					v-model="form.username" 
					placeholder="请输入用户名（至少3个字符）"
					maxlength="20"
				/>
			</view>
			
			<view class="form-group">
				<text class="label">密码</text>
				<input 
					class="input" 
					type="password" 
					v-model="form.password" 
					placeholder="请输入密码（至少6个字符）"
					maxlength="20"
				/>
			</view>
			
			<view class="form-group">
				<text class="label">确认密码</text>
				<input 
					class="input" 
					type="password" 
					v-model="form.confirmPassword" 
					placeholder="请再次输入密码"
					maxlength="20"
				/>
			</view>
			
			<view class="form-group">
				<text class="label">真实姓名</text>
				<input 
					class="input" 
					v-model="form.realname" 
					placeholder="请输入真实姓名"
					maxlength="20"
				/>
			</view>
			
			<view class="form-group">
				<text class="label">角色选择</text>
				<picker 
					class="picker" 
					:value="roleIndex" 
					:range="roleOptions" 
					@change="onRoleChange"
				>
					<view class="picker-text">
						{{ roleOptions[roleIndex] }}
					</view>
				</picker>
			</view>
			
			<button class="register-btn" @click="register" :disabled="loading">
				<text v-if="loading">注册中...</text>
				<text v-else>注册</text>
			</button>
			
			<view class="login-link" @click="goToLogin">
				<text>已有账号？返回登录</text>
			</view>
		</view>
		
		<view class="error-message" v-if="error">
			<text>{{ error }}</text>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			form: {
				username: '',
				password: '',
				confirmPassword: '',
				realname: '',
				role: 'electrician'
			},
			roleOptions: ['电工', '调度员'],
			roleIndex: 0,
			loading: false,
			error: ''
		}
	},
	
	methods: {
		onRoleChange(e) {
			this.roleIndex = e.detail.value;
			this.form.role = this.roleIndex === 0 ? 'electrician' : 'dispatcher';
		},
		
		validateForm() {
			if (!this.form.username.trim()) {
				this.error = '请输入用户名';
				return false;
			}
			
			if (this.form.username.length < 3) {
				this.error = '用户名至少需要3个字符';
				return false;
			}
			
			if (!this.form.password.trim()) {
				this.error = '请输入密码';
				return false;
			}
			
			if (this.form.password.length < 6) {
				this.error = '密码至少需要6个字符';
				return false;
			}
			
			if (this.form.password !== this.form.confirmPassword) {
				this.error = '两次输入的密码不一致';
				return false;
			}
			
			if (!this.form.realname.trim()) {
				this.error = '请输入真实姓名';
				return false;
			}
			
			this.error = '';
			return true;
		},
		
		async register() {
			if (!this.validateForm()) {
				return;
			}
			
			this.loading = true;
			this.error = '';
			
			try {
				const response = await uni.request({
					url: 'http://localhost:5050/api/register',
					method: 'POST',
					data: {
						username: this.form.username,
						password: this.form.password,
						realname: this.form.realname,
						role: this.form.role
					},
					header: {
						'Content-Type': 'application/json'
					}
				});
				
				if (response.statusCode === 200) {
					uni.showToast({
						title: '注册成功',
						icon: 'success'
					});
					
					// 延迟跳转到登录页
					setTimeout(() => {
						uni.navigateTo({
							url: '/pages/login/login'
						});
					}, 1500);
				} else {
					this.error = response.data.msg || '注册失败';
				}
			} catch (err) {
				console.error('注册失败:', err);
				this.error = '网络错误，请稍后重试';
			} finally {
				this.loading = false;
			}
		},
		
		goToLogin() {
			uni.navigateTo({
				url: '/pages/login/login'
			});
		}
	}
}
</script>

<style scoped>
.register-container {
	min-height: 100vh;
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	padding: 40rpx;
	display: flex;
	flex-direction: column;
	justify-content: center;
}

.register-header {
	text-align: center;
	margin-bottom: 60rpx;
}

.logo {
	margin-bottom: 20rpx;
}

.logo-text {
	font-size: 48rpx;
	font-weight: bold;
	color: #fff;
}

.subtitle {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.8);
}

.register-form {
	background: #fff;
	border-radius: 20rpx;
	padding: 60rpx 40rpx;
	box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.1);
}

.form-group {
	margin-bottom: 40rpx;
}

.label {
	display: block;
	font-size: 28rpx;
	color: #333;
	margin-bottom: 20rpx;
	font-weight: 500;
}

.input {
	width: 100%;
	height: 80rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	padding: 0 20rpx;
	font-size: 28rpx;
	background: #f8f9fa;
	box-sizing: border-box;
}

.input:focus {
	border-color: #409eff;
	background: #fff;
}

.picker {
	width: 100%;
	height: 80rpx;
	border: 2rpx solid #e1e5e9;
	border-radius: 10rpx;
	background: #f8f9fa;
	display: flex;
	align-items: center;
	padding: 0 20rpx;
	box-sizing: border-box;
}

.picker-text {
	font-size: 28rpx;
	color: #333;
}

.register-btn {
	width: 100%;
	height: 80rpx;
	background: linear-gradient(135deg, #409eff, #2a6bc5);
	color: #fff;
	border: none;
	border-radius: 10rpx;
	font-size: 32rpx;
	font-weight: 500;
	margin-top: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.register-btn:disabled {
	background: #ccc;
}

.login-link {
	text-align: center;
	margin-top: 40rpx;
}

.login-link text {
	color: #409eff;
	font-size: 28rpx;
}

.error-message {
	background: #fef0f0;
	border: 1rpx solid #fbc4c4;
	color: #f56c6c;
	padding: 20rpx;
	border-radius: 10rpx;
	margin-top: 20rpx;
	text-align: center;
	font-size: 28rpx;
}

/* 响应式设计 */
@media (max-width: 750rpx) {
	.register-container {
		padding: 20rpx;
	}
	
	.register-form {
		padding: 40rpx 30rpx;
	}
	
	.logo-text {
		font-size: 40rpx;
	}
	
	.subtitle {
		font-size: 28rpx;
	}
}
</style> 