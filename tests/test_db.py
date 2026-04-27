from datetime import date

from data.db import filter_conditions


class TestFilterConditions:
    def test_no_filters_returns_empty(self):
        conditions, params = filter_conditions("All", "All", None)
        assert conditions == []
        assert params == []

    def test_company_filter(self):
        conditions, params = filter_conditions("Google", "All", None)
        assert "company = ?" in conditions
        assert params == ["Google"]

    def test_company_all_excluded(self):
        conditions, params = filter_conditions("All", "All", None)
        assert not any("company" in c for c in conditions)

    def test_country_filter(self):
        conditions, params = filter_conditions("All", "United States", None)
        assert "search_country = ?" in conditions
        assert params == ["United States"]

    def test_country_all_excluded(self):
        conditions, params = filter_conditions("All", "All", None)
        assert not any("search_country" in c for c in conditions)

    def test_date_range_filter(self):
        dr = (date(2024, 1, 1), date(2024, 6, 30))
        conditions, params = filter_conditions("All", "All", dr)
        assert "first_seen >= ?" in conditions
        assert "first_seen <= ?" in conditions
        assert date(2024, 1, 1) in params
        assert date(2024, 6, 30) in params

    def test_date_range_none_excluded(self):
        conditions, params = filter_conditions("All", "All", None)
        assert not any("first_seen" in c for c in conditions)

    def test_all_filters_combined(self):
        dr = (date(2024, 3, 1), date(2024, 9, 30))
        conditions, params = filter_conditions("Microsoft", "Canada", dr)
        assert len(conditions) == 4
        assert params == ["Microsoft", "Canada", date(2024, 3, 1), date(2024, 9, 30)]

    def test_company_and_country_no_date(self):
        conditions, params = filter_conditions("Meta", "Germany", None)
        assert len(conditions) == 2
        assert params == ["Meta", "Germany"]

    def test_params_order_company_country_date(self):
        dr = (date(2024, 1, 1), date(2024, 12, 31))
        _, params = filter_conditions("Apple", "India", dr)
        assert params[0] == "Apple"
        assert params[1] == "India"
        assert params[2] == date(2024, 1, 1)
        assert params[3] == date(2024, 12, 31)
