# LOM Dashboard Warehouse Download Debug Flow

## Problem Statement
User reported: "Bonded WH download button produces Excel with headers but no data"
- URL: https://wx-lom-app06.apac.bosch.com:9080/
- Page: **Warehouse Occupation Overview** (HomeCapacity.vue, NOT WareHouseProductBd.vue)
- Button: Download icon next to "Bonded WH (Supplier Cap.:1509)"

## ⚠️ CRITICAL LESSON: Wrong Endpoint Analysis
**Initial mistake**: Analyzed `/excel-product` endpoint from `WareHouseProductBd.vue`
**Actual endpoint**: `/wh/over-2y/export?wh=RDC-BD` from `HomeCapacity.vue`

**Root cause of mistake**: Searched for file names containing "Bonded" or "WH" instead of searching for the exact page title "Warehouse Occupation Overview". Multiple Vue components exist for similar pages.

**Lesson**: ALWAYS search for the exact page title text in the codebase to find the correct component.

---

## Correct Debug Flow

### Phase 1: Front-End Analysis (CORRECT)
**File**: `source code/src/views/Home/HomeCapacity.vue` (line 9: "Warehouse Occupation Overview")

```javascript
// Line 150-153: Download button handler
handleDownLoad(name) {
  window.open(
    `${process.env.VUE_APP_BASE_URL}/wh/over-2y/export?wh=${name}`
  );
},
```

**Button binding** (line 50-52):
```html
@click.stop="handleDownLoad(item.name == 'RDC-WF' ? 'RBCD-WX03' : item.name)"
```

**API Call**: `GET /api/wh/over-2y/export?wh=RDC-BD`

### Phase 2: Backend Analysis (CORRECT)
**Controller**: `WHLoiOver2yStockController.java`
```java
@RequestMapping(value = "/over-2y/export", method = RequestMethod.GET)
public void exportSheet(HttpServletRequest request,
                        HttpServletResponse response,
                        @RequestParam(value = "wh", required = false) String wh,
                        @RequestParam(value = "title", required = false) String title) {
    LoiVOver2yStock loiVOver2yStock = new LoiVOver2yStock();
    loiVOver2yStock.setWh(wh);
    List<LoiVOver2yStock> list = this.loiVOver2yStockMapper.getByPage(schema, loiVOver2yStock);
    // ... export to Excel using EasyPOI
}
```

**Mapper XML**: `LoiVOver2yStockMapper.xml`
```xml
<select id="getByPage" resultType="com.touchspring.lomkpi.domain.entity.LoiVOver2yStock">
    select * from ${schema}.LOI_V_OVER_2Y_STOCK where 1 = 1
    <if test="params.wh != null and params.wh != ''">
      and upper(wh) = upper(#{params.wh,jdbcType=VARCHAR})
    </if>
</select>
```

**Actual SQL**: `SELECT * FROM logpoe.LOI_V_OVER_2Y_STOCK WHERE UPPER(wh) = UPPER('RDC-BD')`

### Phase 3: Database Investigation

**Target table**: `LOI_V_OVER_2Y_STOCK` (NOT `FACT_V_WH_PRODUCT_DW`)

To be verified:
```sql
SELECT COUNT(*) FROM LOGPOE.LOI_V_OVER_2Y_STOCK;
SELECT COUNT(*) FROM LOGPOE.LOI_V_OVER_2Y_STOCK WHERE UPPER(wh) = 'RDC-BD';
SELECT OBJECT_NAME, OBJECT_TYPE, STATUS FROM ALL_OBJECTS WHERE OBJECT_NAME = 'LOI_V_OVER_2Y_STOCK' AND OWNER = 'LOGPOE';
```

---

## Wrong Analysis (for reference - do NOT repeat this mistake)

### What was analyzed incorrectly:
- `WareHouseProductBd.vue` → `/excel-product` → `FACT_V_WH_PRODUCT_DW`
- This is a DIFFERENT page (Bonded WH detail page), not the Warehouse Occupation Overview page

### Why the mistake happened:
1. Searched for "Bonded" in code, found `WareHouseProductBd.vue`
2. Assumed this was the page with the download button
3. Never verified by checking the page title against the user's screenshot
4. Spent many rounds debugging the wrong endpoint

---

## Key Learnings

1. **Page title is the anchor**: Search for the exact page title ("Warehouse Occupation Overview") to find the correct Vue component
2. **Multiple components for similar pages**: `HomeCapacity.vue` (overview) vs `WareHouseProductBd.vue` (detail) both relate to Bonded WH but are different pages
3. **Download button ≠ page data API**: The download button may call a completely different API than the page's data loading API
4. **Verify before deep-diving**: Confirm the API path by reading the button's click handler before analyzing backend code

## Related Objects (CORRECT)
| Object | Type | Schema | Purpose |
|--------|------|--------|---------|
| LOI_V_OVER_2Y_STOCK | TABLE/VIEW | LOGPOE | Download data source for over-2y stock |
| FACT_V_WH_PRODUCT_DW | VIEW | LOGPOE | Page data source (NOT download source) |
| LOI_V_WH_OVERVIEW | MATERIALIZED VIEW | LOGPOE | Overview page pie chart data |
