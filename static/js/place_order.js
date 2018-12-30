$(function () {
    $('#order_btn').click(function () {
        // 获取用户选择的地址id,支付方式,要购买的商品id
        addr_id = $('input[name="addr_id"]:checked').val();
        pay_method = $('input[name="pay_style"]:checked').val();
        sku_ids = $(this).attr('sku_ids');
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params = {
          'addr_id': addr_id,
          'pay_method': pay_method,
          'sku_ids': sku_ids,
          'csrfmiddlewaretoken': csrf
        };
        $.post('/order/commit', params, function (data) {
            if(data.res == 5) {
                //alert(data.message);
                window.location.href = '/user/order/1'
            } else {
                alert(data.errmsg);
            }
        });

    });
});