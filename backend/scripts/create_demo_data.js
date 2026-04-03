/**
 * Demo数据创建脚本
 * 通过API直接创建完整的测试数据
 */

const API_BASE = 'http://localhost:8000/api/v1';

// 随机UUID生成
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function createDemoData() {
  console.log('=' .repeat(50));
  console.log('开始创建Demo测试数据...');
  console.log('=' .repeat(50));

  try {
    // 1. 登录获取token
    console.log('\n[1/7] 登录系统...');
    let loginResponse = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=demo&password=demo123`
    });

    let token;
    if (loginResponse.ok) {
      const loginData = await loginResponse.json();
      token = loginData.access_token;
      console.log('  ✓ 登录成功');
    } else {
      // 尝试注册新用户
      console.log('  → 用户不存在，尝试注册...');
      const registerResponse = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'demo',
          password: 'Demo123',
          email: 'demo@example.com'
        })
      });

      if (registerResponse.ok) {
        console.log('  ✓ 注册成功');
        await sleep(500);
        // 重新登录
        loginResponse = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: `username=demo&password=Demo123`
        });
        const loginData = await loginResponse.json();
        token = loginData.access_token;
        console.log('  ✓ 登录成功');
      } else {
        throw new Error('注册失败');
      }
    }

    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    // 2. 获取或创建测试项目
    console.log('\n[2/7] 获取测试项目...');
    // 首先尝试获取现有的项目
    let project;
    try {
      // 通过auth API获取用户信息来找到项目
      // 暂时使用固定ID，实际应该从用户数据获取
      const projectId = '6169172c-1c5b-43a3-b039-6e1f2a7d1c5c'; // 已知的项目ID
      console.log(`  → 使用现有项目ID: ${projectId}`);
      project = { id: projectId, name: 'Demo项目' };
    } catch (e) {
      console.log('  ⚠ 无法获取项目，请确保数据库中有项目数据');
      throw new Error('需要先创建项目');
    }

    // 3. 创建测试任务
    console.log('\n[3/7] 创建测试任务...');
    const taskResponse = await fetch(`${API_BASE}/ui/tasks/?project_id=${project.id}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: '百度搜索测试',
        description: '演示百度搜索功能的UI自动化测试',
        tags: ['demo', 'ui', 'baidu']
      })
    });

    let task;
    if (taskResponse.ok) {
      task = await taskResponse.json();
      console.log(`  ✓ 创建任务: ${task.name} (ID: ${task.id})`);
    } else {
      throw new Error('创建任务失败');
    }

    // 4. 创建测试场景
    console.log('\n[4/7] 创建测试场景...');
    const scenarioResponse = await fetch(`${API_BASE}/ui/scenarios/?task_id=${task.id}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: '百度搜索场景',
        description: '在百度首页搜索关键词并验证结果',
        tags: ['搜索', '冒烟测试']
      })
    });

    let scenario;
    if (scenarioResponse.ok) {
      scenario = await scenarioResponse.json();
      console.log(`  ✓ 创建场景: ${scenario.name} (ID: ${scenario.id})`);
    } else {
      throw new Error('创建场景失败');
    }

    // 5. 创建测试用例
    console.log('\n[5/7] 创建测试用例...');
    const caseResponse = await fetch(`${API_BASE}/ui/scenarios/${scenario.id}/cases`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: '搜索关键词测试用例',
        description: '打开百度首页，输入关键词并搜索',
        priority: 'P1',
        tags: ['搜索', '核心功能']
      })
    });

    let testCase;
    if (caseResponse.ok) {
      testCase = await caseResponse.json();
      console.log(`  ✓ 创建用例: ${testCase.name} (ID: ${testCase.id})`);
    } else {
      throw new Error('创建用例失败');
    }

    // 6. 获取关键字
    console.log('\n[6/7] 获取测试关键字...');
    const keywordsResponse = await fetch(`${API_BASE}/ui/keywords/?enabled_only=false`);
    const keywords = await keywordsResponse.json();
    const keywordMap = {};
    for (const kw of keywords) {
      keywordMap[kw.name] = kw;
    }
    console.log(`  ✓ 找到 ${keywords.length} 个关键字`);

    // 7. 创建测试步骤
    console.log('\n[7/7] 创建测试步骤...');
    const stepsToCreate = [];

    if (keywordMap['NAVIGATE']) {
      stepsToCreate.push({
        step_order: 0,
        keyword_id: keywordMap['NAVIGATE'].id,
        step_name: '打开百度首页',
        parameters: { url: 'https://www.baidu.com' }
      });
      console.log('  ✓ 步骤1: 打开百度首页');
    }

    if (keywordMap['INPUT']) {
      stepsToCreate.push({
        step_order: 1,
        keyword_id: keywordMap['INPUT'].id,
        step_name: '输入搜索关键词',
        parameters: {
          selector: '#kw',
          text: '测试自动化平台',
          clear_first: true
        }
      });
      console.log('  ✓ 步骤2: 输入搜索关键词');
    }

    if (keywordMap['CLICK']) {
      stepsToCreate.push({
        step_order: 2,
        keyword_id: keywordMap['CLICK'].id,
        step_name: '点击搜索按钮',
        parameters: { selector: '#su', timeout: 5000 }
      });
      console.log('  ✓ 步骤3: 点击搜索按钮');
    }

    if (keywordMap['WAIT_FOR_ELEMENT']) {
      stepsToCreate.push({
        step_order: 3,
        keyword_id: keywordMap['WAIT_FOR_ELEMENT'].id,
        step_name: '等待搜索结果',
        parameters: {
          selector: '.result',
          state: 'visible',
          timeout: 10000
        }
      });
      console.log('  ✓ 步骤4: 等待搜索结果');
    }

    // 批量创建步骤
    for (const stepData of stepsToCreate) {
      const stepResponse = await fetch(`${API_BASE}/ui/scenarios/cases/${testCase.id}/steps`, {
        method: 'POST',
        headers,
        body: JSON.stringify(stepData)
      });

      if (!stepResponse.ok) {
        console.error(`  ✗ 创建步骤失败: ${stepData.step_name}`);
      }
    }

    console.log('\n' + '='.repeat(50));
    console.log('Demo数据创建完成!');
    console.log('='.repeat(50));
    console.log(`\n项目ID: ${project.id}`);
    console.log(`任务ID: ${task.id}`);
    console.log(`场景ID: ${scenario.id}`);
    console.log(`用例ID: ${testCase.id}`);
    console.log(`步骤数: ${stepsToCreate.length}`);
    console.log(`\n访问 http://localhost:3001 查看效果`);
    console.log(`\n或使用以下命令测试任务:`);
    console.log(`  curl -X POST http://localhost:8000/api/v1/ui/tasks/${task.id}/execute \\`);
    console.log(`    -H "Authorization: Bearer ${token}"`);

  } catch (error) {
    console.error('\n❌ 错误:', error.message);
    process.exit(1);
  }
}

// 执行创建
createDemoData();
