// Toast/Message 通知组件
export const message = {
  success: (text: string) => {
    console.log('✅ Success:', text)
    // 可以集成 toast 库，这里简化处理
    alert(text)
  },
  error: (text: string) => {
    console.error('❌ Error:', text)
    alert(text)
  },
  info: (text: string) => {
    console.log('ℹ️ Info:', text)
    alert(text)
  },
  warning: (text: string) => {
    console.warn('⚠️ Warning:', text)
    alert(text)
  },
}
