$(function () {
    $('.add-to-cart').click(function () {
       // 得到sku_id 和 商品的个数
        sku_id = $(this).attr('sku_id');
        count = 1;
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params = {
            'sku_id': sku_id,
            'count': count,
            'csrfmiddlewaretoken': csrf
        };
        $.post('/cart/add', params, function (data) {
            if(data.res == 5) {
                window.location.href = '/cart/info';
            } else {
                alert(data.errmsg);
            }
        })
    });
});