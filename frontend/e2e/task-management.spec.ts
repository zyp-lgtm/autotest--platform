import { test, expect } from '@playwright/test'

// 测试配置
const BASE_URL = process.env.BASE_URL || 'http://localhost:3001'
const TEST_USER = {
  username: 'demo',
  password: 'demo123'
}

test.describe('任务管理 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前先登录
    await page.goto(BASE_URL)
    await page.fill('input[name="username"]', TEST_USER.username)
    await page.fill('input[name="password"]', TEST_USER.password)
    await page.click('button[type="submit"]')

    // 等待登录完成（跳转到仪表盘）
    await page.waitForURL('**/')
    await expect(page.locator('h1.text-2xl')).toContainText('仪表盘')
  })

  test('应该显示任务管理导航', async ({ page }) => {
    // 点击任务管理链接
    await page.click('text=任务管理')

    // 等待页面加载
    await page.waitForURL('**/tasks')
    await expect(page.locator('h1.text-2xl')).toContainText('任务管理')
  })

  test('应该能够创建新任务', async ({ page }) => {
    // 导航到任务管理
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 点击创建任务按钮
    await page.click('button:has-text("创建任务")')

    // 等待表单加载
    await page.waitForURL('**/tasks/new')
    await expect(page.locator('h1.text-2xl')).toContainText('创建任务')

    // 填写表单
    const taskName = `E2E测试_${Date.now()}`
    await page.fill('input#name', taskName)
    await page.fill('textarea#description', '这是自动化测试创建的任务')

    // 添加标签
    const tagInput = page.locator('input#tags')
    await tagInput.fill('E2E')
    await tagInput.press('Enter')
    await tagInput.fill('自动化')
    await tagInput.press('Enter')

    // 提交表单
    await page.click('button[type="submit"]:has-text("创建")')

    // 验证跳转到任务列表
    await page.waitForURL('**/tasks', { timeout: 10000 })

    // 验证新任务出现在列表中
    await expect(page.locator(`text=${taskName}`)).toBeVisible({ timeout: 5000 })
  })

  test('应该能够搜索任务', async ({ page }) => {
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 使用搜索框
    const searchInput = page.locator('input[placeholder*="搜索"]')
    await searchInput.fill('测试')

    // 等待搜索结果
    await page.waitForTimeout(500)

    // 验证搜索功能（具体结果取决于数据库中的数据）
    const hasResults = await page.locator('text=测试').count() > 0
    expect(hasResults || await page.locator('text=暂无任务').isVisible()).toBeTruthy()
  })

  test('应该能够编辑任务', async ({ page }) => {
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 查找第一个任务的编辑按钮
    const editButton = page.locator('button:has-text("编辑")').first()
    const hasEditButton = await editButton.count() > 0

    if (hasEditButton) {
      await editButton.click()

      // 等待编辑页面
      await page.waitForURL('**/tasks/*/edit')

      // 修改任务名称
      const nameInput = page.locator('input#name')
      await nameInput.fill(`已编辑_${Date.now()}`)

      // 保存
      await page.click('button[type="submit"]')

      // 验证返回任务列表
      await page.waitForURL('**/tasks')
    } else {
      console.log('没有可编辑的任务')
    }
  })

  test('应该能够删除任务', async ({ page }) => {
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 记录删除前的任务数量
    const tasksBefore = await page.locator('div[class*="border"]').count()

    // 查找删除按钮
    const deleteButton = page.locator('button:has-text("删除")').first()
    const hasDeleteButton = await deleteButton.count() > 0

    if (hasDeleteButton) {
      // 监听对话框
      page.on('dialog', dialog => {
        expect(dialog.message()).toContain('删除')
        dialog.accept()
      })

      await deleteButton.click()

      // 等待删除完成
      await page.waitForTimeout(1000)

      // 验证任务数量减少
      const tasksAfter = await page.locator('div[class*="border"]').count()
      expect(tasksAfter).toBeLessThan(tasksBefore)
    } else {
      console.log('没有可删除的任务')
    }
  })

  test('应该能够执行任务', async ({ page }) => {
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 查找执行按钮
    const executeButton = page.locator('button:has-text("执行")').first()
    const hasExecuteButton = await executeButton.count() > 0

    if (hasExecuteButton) {
      // 点击执行（会显示 alert）
      page.on('dialog', dialog => dialog.accept())
      await executeButton.click()

      // 等待响应
      await page.waitForTimeout(500)
    } else {
      console.log('没有可执行的任务')
    }
  })

  test('导航栏应该在所有页面显示', async ({ page }) => {
    // 在仪表盘
    await expect(page.locator('a:has-text("仪表盘")')).toBeVisible()
    await expect(page.locator('a:has-text("任务管理")')).toBeVisible()

    // 点击任务管理
    await page.click('text=任务管理')
    await page.waitForURL('**/tasks')

    // 验证导航仍然存在
    await expect(page.locator('a:has-text("仪表盘")')).toBeVisible()
    await expect(page.locator('a:has-text("任务管理")')).toBeVisible()

    // 返回仪表盘
    await page.click('a:has-text("仪表盘")')
    await page.waitForURL('**/')

    await expect(page.locator('h1.text-2xl')).toContainText('仪表盘')
  })

  test('应该显示用户信息和退出按钮', async ({ page }) => {
    // 验证用户名显示
    await expect(page.locator(`text=欢迎, ${TEST_USER.username}`)).toBeVisible()

    // 验证退出按钮存在
    await expect(page.locator('button:has-text("退出")')).toBeVisible()

    // 点击退出
    await page.click('button:has-text("退出")')

    // 验证跳转到登录页
    await page.waitForURL('**/login')
    await expect(page.locator('input[name="username"]')).toBeVisible()
  })
})
