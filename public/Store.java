import java.time.LocalDate;

public class Store {

    protected String name;
    private LocalDate openingDate;

    private Product[] products;
    public int productSize;
    private int productCapacity;

    private Order[] orders;
    private int orderSize;
    private int orderCapacity;

    public Store(String name, LocalDate openingDate, int productCapacity, int orderCapacity){

        // There might be something you need to do here, maybe throwing to the caller?

        this.name = name.trim();
        this.openingDate = openingDate;

        this.productCapacity = productCapacity;
        this.orderCapacity = orderCapacity;

        this.products = new Product[productCapacity];
        this.orders = new Order[orderCapacity];

        this.productSize = 0;
        this.orderSize = 0;
    }

    public String getName() { return name; }
    public LocalDate getOpeningDate() { return openingDate; }

    public Product[] getProducts() { return products; }
    public int getProductSize() { return productSize; }
    public int getProductCapacity() { return productCapacity; }

    public Order[] getOrders() { return orders; }
    public int getOrderSize() { return orderSize; }
    public int getOrderCapacity() { return orderCapacity; }

    public boolean addProduct(Product product){

        // There might be something you need to do here, maybe throwing to the caller?

        products[productSize] = product;
        productSize++;
        return true;
    }

    public boolean updateProduct(Product target, Product replacement){

        // There might be something you need to do here, maybe throwing to the caller?

        int idx = indexOfProduct(target);
        // There might be something you need to do here, maybe throwing to the caller?


        products[idx] = replacement;
        return true;
    }

    //nothing to change here.
    public Product searchProductByName(String name) {
        if (name == null) return null;
        for (int i = 0; i < productSize; i++) {
            if (products[i] != null && products[i].getName() != null
                    && products[i].getName().equalsIgnoreCase(name)) {
                return products[i];
            }
        }
        return null;
    }

    //nothing to change here.
    public Product getProductAt(int index) throws RecordNotFoundException{
    
        // Index should map to an existing stored record.
        if (index < 0 || index >= productSize) {
            throw new RecordNotFoundException("product index out of range.");
        }

        return products[index];
    }

    public boolean createOrder(Order order){
        
        // There might be something you need to do here, maybe throwing to the caller?

        Product p = searchProductByName(order.getProductName());
        // There might be something you need to do here, maybe throwing to the caller?

        boolean deducted = p.deductStock(order.getAmount());
        // There might be something you need to do here, maybe throwing to the caller?

        orders[orderSize] = order;
        orderSize++;
        return true;
    }

    public boolean cancelOrder(String orderId){

        // There might be something you need to do here, maybe throwing to the caller?

        Order o = orders[idx];
        Product p = searchProductByName(o.getProductName());
        
        // Restoration requires the referenced product to exist. I give this to you.
        if (p == null) {
            throw new RecordNotFoundException("product for this order not found (cannot restore stock).");
        }

        p.restock(o.getAmount());

        // Removal should keep the array compact (no gaps). I give this to you too. Dont bother.
        for (int i = idx; i < orderSize - 1; i++) {
            orders[i] = orders[i + 1];
        }
        orders[orderSize - 1] = null;
        orderSize--;

        return true;
    }

    //nothing to change here.
    public Order searchOrderById(String orderId) {
        if (orderId == null) return null;
        for (int i = 0; i < orderSize; i++) {
            if (orders[i] != null && orders[i].getOrderId() != null
                    && orders[i].getOrderId().equalsIgnoreCase(orderId)) {
                return orders[i];
            }
        }
        return null;
    }

    //nothing to change here
    public Order getOrderAt(int index) throws RecordNotFoundException {
        if (index < 0 || index >= orderSize) {
            throw new RecordNotFoundException("order index out of range.");
        }
        return orders[index];
    }

    private int indexOfProduct(Product target) {
        for (int i = 0; i < productSize; i++) {
            if (products[i] == target) return i; // identity match
        }
        return -1;
    }

    private int indexOfOrderById(String orderId) {
        for (int i = 0; i < orderSize; i++) {
            if (orders[i] != null && orders[i].getOrderId() != null
                    && orders[i].getOrderId().equalsIgnoreCase(orderId)) {
                return i;
            }
        }
        return -1;
    }
}
