country_locator = 'select#country a'
subcategory_locator = '#menu>ul>li:nth_child(3)>ul a, #menu>ul>li:nth_child(4)>ul a, ' \
                      '#menu>ul>li:nth_child(5)>ul a, #menu>ul>li:nth_child(6)>ul a'
product_locator = 'a.name._item'
script_tag_data_extract = "//script[@data-compress='true']"
product_re = '"product":(.*),"parent'
countrycode_re = "countryCode: *'(.*?)'"
currencycode_re = 'currencyCode":"(.*?)"'
