from jackhelper import autodealer

from .utils import daysInYear

import datetime



class Stats:
    def __init__(
        self, city: str, 
        start_date: datetime.date, 
        end_date: datetime.date,
    ):
        self.city = city
        self.start_date = start_date
        self.end_date = end_date
        self.blocks_methods = {
            'finance': self.financeBlock,
            'orders': self.ordersBlock,
            'diagnostic_packages': self.diagnosticPackagesBlock,
        }


    def getMetrics(self, block_id: str, short_output: bool = False) -> dict:
        if block_id in self.blocks_methods.keys():
            self.cursor = autodealer.connect(self.city)

            self.short_output = short_output
            block_method = self.blocks_methods[block_id]
            block_metrics = block_method()

            self.cursor.close()
            return {'block_id': block_id, 'metrics': block_metrics}
        else:
            raise ValueError('Unavailable block_id')


    def fetch(self, query: str, fetch_type: str, indexes: list = None, zero_if_none=False):
        response = self.cursor.execute(query % (self.start_date, self.end_date))
        match fetch_type:
            case 'one': response = response.fetchone()
            case 'all': response = response.fetchall()
        if indexes:
            for i in indexes:
                response = response[0]
        if zero_if_none and response is None:
            return 0
        return response


    def financeBlock(self) -> list:
        metrics = []

        works_revenue_query = '''
            SELECT SUM(SUMMA_WORK)
            FROM DOCUMENT_SERVICE_DETAIL ds
            JOIN DOCUMENT_OUT_HEADER doh
            ON ds.DOCUMENT_OUT_HEADER_ID = doh.DOCUMENT_OUT_HEADER_ID
            WHERE doh.DATE_CREATE BETWEEN timestamp '%s 00:00' AND timestamp '%s 23:59'
            AND doh.DOCUMENT_TYPE_ID = 11
            AND doh.STATE = 4
        '''
        works_revenue = self.fetch(
            works_revenue_query, 
            fetch_type='one', 
            indexes=[0], 
            zero_if_none=True
        )
        metrics.append({
            'id': 'works_revenue', 
            'title': 'Выручка с работ', 
            'value': float(works_revenue), 
            'unit': '₽'
        })

        spare_parts_revenue_query = '''
                SELECT SUM(COST * GOODS_COUNT)
                FROM GOODS_OUT go
                JOIN DOCUMENT_OUT do
                ON go.DOCUMENT_OUT_ID = do.DOCUMENT_OUT_ID
                JOIN DOCUMENT_OUT_HEADER doh
                ON do.DOCUMENT_OUT_ID = doh.DOCUMENT_OUT_ID
                WHERE doh.DATE_CREATE BETWEEN timestamp '%s 00:00' AND timestamp '%s 23:59'
                AND doh.DOCUMENT_TYPE_ID IN (2, 3, 11)
                AND STATE = 4
        '''
        spare_parts_revenue = self.fetch(
            spare_parts_revenue_query, 
            fetch_type='one', 
            indexes=[0], 
            zero_if_none=True
        )
        metrics.append({
            'id': 'spare_parts_revenue', 
            'title': 'Выручка с з/ч',
            'value': float(spare_parts_revenue), 
            'unit': '₽'
        })

        revenue = works_revenue + spare_parts_revenue
        metrics.insert(0, {
            'id': 'revenue',
            'title': 'Выручка',
            'value': float(revenue),
            'unit': '₽',
        })  

        if self.short_output is False:
            days_in_year = daysInYear()
            s = Stats(
                self.city, 
                self.start_date-datetime.timedelta(days=days_in_year),
                self.end_date-datetime.timedelta(days=days_in_year),
            )

            orders_count = s.getMetrics('orders', short_output=True)['metrics'][0]['value']
            try:
                average_check = float(revenue) / orders_count
            except ZeroDivisionError:
                average_check = 0
            metrics.append({
                'id': 'average_check',
                'title': 'Средний чек',
                'value': average_check,
                'unit': '₽',
            })  

            last_year_metrics = s.getMetrics('finance', short_output=True)['metrics']
            last_year_revenue = last_year_metrics[0]['value']
            last_year_works_revenue = last_year_metrics[1]['value']
            last_year_spare_parts_revenue = last_year_metrics[2]['value']

            try:
                growth_trend = round(float(revenue) / last_year_revenue * 100 - 100, 2)
            except ZeroDivisionError:
                if revenue > 0: growth_trend = 0
                else: growth_trend = 100

            metrics.append({
                'id': 'growth_trend', 
                'title': 'Рост год к году',
                'value': growth_trend, 
                'unit': '%',
                'submetrics': last_year_metrics,
                'submetrics_unit': '₽',
            })

        return metrics


    def ordersBlock(self) -> list:
        metrics = []

        only_total_count = '''
            COUNT(DISTINCT doh.DOCUMENT_OUT_HEADER_ID) AS total_orders
        '''
        each_count = '''
            COUNT(DISTINCT doh.DOCUMENT_OUT_HEADER_ID) AS total_orders,
            COUNT(DISTINCT CASE 
                WHEN (ds.SPECIAL_NOTES IS NULL OR CHAR_LENGTH(ds.SPECIAL_NOTES) < 20) 
                THEN doh.DOCUMENT_OUT_HEADER_ID 
            END) AS orders_without_recommendations,
            COUNT(DISTINCT CASE 
                WHEN (ds.RUN_DURING IS NULL OR ds.RUN_BEFORE IS NULL) 
                THEN doh.DOCUMENT_OUT_HEADER_ID 
            END) AS orders_without_mileage,
            COUNT(DISTINCT CASE 
                WHEN ds.REASONS_APPEAL IS NULL 
                THEN doh.DOCUMENT_OUT_HEADER_ID 
            END) AS orders_without_reasons_appeal,
            COUNT(DISTINCT CASE 
                WHEN sw.DISCOUNT_WORK > 0 AND sw.DISCOUNT_WORK <= 10 
                THEN doh.DOCUMENT_OUT_HEADER_ID 
            END) AS orders_with_discount_lte_10
        '''

        orders_count_query = '''
            SELECT 
                {columns_list}
            FROM DOCUMENT_OUT_HEADER doh
            LEFT JOIN DOCUMENT_SERVICE_DETAIL ds
                ON doh.DOCUMENT_OUT_HEADER_ID = ds.DOCUMENT_OUT_HEADER_ID
            LEFT JOIN SERVICE_WORK sw
                ON doh.DOCUMENT_OUT_ID = sw.DOCUMENT_OUT_ID
            WHERE doh.DATE_CREATE BETWEEN timestamp '%s 00:00' AND timestamp '%s 23:59'
            AND doh.DOCUMENT_TYPE_ID = 11
            AND doh.STATE = 4;
        '''.format(
            columns_list=only_total_count if self.short_output else each_count
        )

        orders = self.fetch(orders_count_query, fetch_type='one')
        orders_count = orders[0]
        orders_count_metric = {
            'id': 'orders_count', 
            'title': 'Всего', 
            'value': orders_count, 
            'unit': 'шт.'
        }
        if self.short_output is False:
            orders_count_metric['submetrics'] = [
                {'title': 'Без рекомендаций', 'value': orders[1]},
                {'title': 'Без пробега', 'value': orders[2]},
                {'title': 'Без причин обращения', 'value': orders[3]},
                {'title': 'Со скидкой до 11%', 'value': orders[4]},
            ]

            orders_with_discount_gte_11_query = '''
                SELECT 
                    FLOOR(sw.DISCOUNT_WORK) AS discount_percentage,
                    COUNT(*) AS discount_count
                FROM SERVICE_WORK sw
                JOIN DOCUMENT_OUT_HEADER doh
                    ON sw.DOCUMENT_OUT_ID = doh.DOCUMENT_OUT_ID
                WHERE sw.DISCOUNT_WORK > 10
                AND doh.DATE_CREATE BETWEEN timestamp '%s 00:00' AND timestamp '%s 23:59'
                AND doh.DOCUMENT_TYPE_ID = 11
                AND doh.STATE = 4
                GROUP BY FLOOR(sw.DISCOUNT_WORK)
                ORDER BY discount_percentage;

            '''
            orders_with_discount_gte_11 = self.fetch(orders_with_discount_gte_11_query, fetch_type='all')
            orders_with_discount_gte_11_metric = {
                'id': 'orders_with_discount_gte_11', 
                'title': 'ЗН со скидкой от 11%',
                'unit': 'шт.'
            }
            orders_with_discount_gte_11_count = 0
            if orders_with_discount_gte_11:
                orders_with_discount_gte_11_metric['submetrics'] = []
                for i in orders_with_discount_gte_11:
                    percent = int(i[0])
                    count = i[1]
                    orders_with_discount_gte_11_count += count
                    orders_with_discount_gte_11_metric['submetrics'].append({
                        'title': f'{percent} %', 'value': count,
                    })
            orders_with_discount_gte_11_metric['value'] = orders_with_discount_gte_11_count
            metrics.append(orders_with_discount_gte_11_metric)

        metrics.insert(0, orders_count_metric)
        return metrics


    def diagnosticPackagesBlock(self) -> list:
        metrics = []

        packages_sold_query = '''
            SELECT COUNT(ds.DOCUMENT_SERVICE_DETAIL_ID)
            FROM DOCUMENT_SERVICE_DETAIL ds
            JOIN DOCUMENT_OUT_HEADER doh 
                ON ds.DOCUMENT_OUT_HEADER_ID = doh.DOCUMENT_OUT_HEADER_ID
            JOIN SERVICE_WORK sw 
                ON doh.DOCUMENT_OUT_ID = sw.DOCUMENT_OUT_ID
            WHERE ds.DATE_START BETWEEN timestamp '%s 00:00' AND timestamp '%s 23:59'
            AND doh.DOCUMENT_TYPE_ID = 11
            AND doh.STATE = 4
            AND sw.NAME = 'Пакет диагностик при ТО';
        '''
        packages_sold = self.fetch(
            packages_sold_query, 
            fetch_type='one',
            indexes=[0],
            zero_if_none=True
        )
        metrics.append({
            'id': 'packages_sold', 
            'title': 'Продано', 
            'value': packages_sold, 
            'unit': 'шт.'
        })
        return metrics