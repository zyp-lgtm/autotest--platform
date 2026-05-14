import uuid
from app.services.recording.data_extractor import DataExtractor


class TestGenerateTestData:
    def test_generates_single_base_row_only(self):
        """generate_test_data 只应生成 1 行基准数据，不生成变体"""
        extractor = DataExtractor()
        from app.services.recording.data_extractor import DataPattern
        patterns = [
            DataPattern(
                id=str(uuid.uuid4()),
                field_name="username",
                pattern_type="input",
                values=["admin"],
                confidence=0.9,
                selected=True,
                suggested_variations=["admin_test", "", "a" * 20]
            ),
            DataPattern(
                id=str(uuid.uuid4()),
                field_name="password",
                pattern_type="input",
                values=["123456"],
                confidence=0.9,
                selected=True,
                suggested_variations=["123456_test", ""]
            ),
        ]

        result = extractor.generate_test_data(patterns, "测试场景", str(uuid.uuid4()))

        assert result["name"] == "测试场景_测试数据"
        assert result["data_type"] == "json"
        assert len(result["data"]) == 1, f"应只有 1 行基准数据，实际 {len(result['data'])} 行"
        assert result["data"][0] == {"username": "admin", "password": "123456"}
